Title: Image Stream Processing to Blob Storage
Date: 2015-09-11 16:08
Author: noodlefrenzy
Category: Software
Tags: .NET, ASP.Net, Azure, Azure Blob, C#, SQL Azure
Slug: image-stream-processing-to-blob-storage
Status: published

I was recently working on a project to train [Deep
ConvNets](http://www.readcube.com/articles/10.1038%2Fnature14539?shared_access_token=DaxW8O-3gQoqte9kXFFUANRgN0jAjWel9jnR3ZoTv0PU8PImtLRceRBJ32CtadUBIC1dchyTLE3_1-FCJeTkHXnB0vI4SmupYf4v2t_dG6HjI9FdSJMFDQ6iWCA7T6tcte2-dAp-SzhLtuCkfPvhI6x--H5W98_7bqOVwSnqt1Vqo6bzZ5ZM7lCIPdavoThMMSXBgYmSjKSk0CrGtb5KUw%3D%3D)
for image recognition tasks, and ran into several interesting problems
along the way. This post is the first in a series outlining some of
those problems and how I went about solving them, and it focuses on the
problem of image uploads to Azure Blob storage. As always, the
MIT-licensed code is [on
GitHub](https://github.com/noodlefrenzy/asp-blob-uploader).

The crux of the issue: we had a deployed neural net out there just
waiting for images to come in and be scored, and I'd deployed an ASP.Net
service for handling image uploads. Two problems: I needed to transform
those images prior to scoring, and I wanted to make sure I didn't write
them to the local file system if possible (as a crash would leave
hanging files and fill up the disk).

Uploading Files
---------------

On the web, the typical way you upload files hasn't changed all that
much in over a decade - most people use a multi-part form submission
with MIME-encoded content. Using this format for a simple captioned
picture, the resulting payload looks something like:

```
POST ...
Content-Type: multipart/form-data; boundary=---------------------------8675309

-----------------------------8675309
Content-Disposition: form-data; name="description"

Look at this epic sandwich
-----------------------------8675309
Content-Disposition: form-data; name="image1"; filename="EpicSandwich.jpg"
Content-Type: image/jpeg

...bits...
-----------------------------8675309--
```

Note the form data is all in one section, and the files are each in
their own MIME-encoded section with included filenames.

Processing Files In ASP.Net
---------------------------

Mike Wasson has [a great blog
post](http://www.asp.net/web-api/overview/advanced/sending-html-form-data,-part-2)with
explicit instructions on how to process multi-part form data from within
ASP.Net. To summarize, you need to instantiate
a `MultipartFormDataStreamProvider` pointed to where you want to store
the files on disk, and then use `ReadAsMultipartAsync` to put them
there. It does the decoding and stores things correctly, but the problem
is that if you crash at any point during this process, you've just left
files littering the disk.

There are a few different ways around this (detecting the files on
startup, clearing temp on restart, etc.), but since I wanted to
pre-process the image before storing it anyway, I decided to seek
another solution. Ultimately, I wanted to take the incoming data stream,
process it, and then store it directly into Azure Blob storage. For
that, I would need a custom form data processor.

Building a Blob Stream Provider
-------------------------------

There seem to be two main steps in switching away from local file
storage to Azure Blob store - first create a Stream capable of storing
to an Azure Blob, and then create a provider to return those streams.
Then, when `ReadAsMultipartAsync` gets called, it'll store those files
into blobs for you. In reality, it's slightly more complicated since it
doesn't seem to guarantee a call to Close on the stream, so it's tough
to know when to write it to blob storage, so I would up implementing my
custom Stream as a wrapper around a MemoryStream and then giving my
custom Provider a SaveAll method to push everything to the cloud.

#### Customizing a Stream

My custom Stream is a simple wrapper around a `MemoryStream` with some
sugar to massage the filename into blob-friendly format, and a helper
method to do the actual upload:

```csharp
public class MultipartBlobStream : Stream
{
    public MultipartBlobStream(CloudBlobContainer container, string filename, string extension)
    {
        extension = extension.ToLowerInvariant().TrimStart('.');
        if (filename.EndsWith(extension))
        {
            filename = filename.Substring(0, filename.Length - 1 - extension.Length);
        }
        this.blobContainer = container;
        this.FileName = filename;
        this.Extension = extension;
    }

    private CloudBlobContainer blobContainer;
    private MemoryStream underlyingStream = new MemoryStream();
    public string FileName { get; set; }
    public string Extension { get; set; }

    public override bool CanRead { get { return this.underlyingStream.CanRead; } }
    // ... other Stream overrides delegating to underlyingStream

    public string BlobPath()
    {
        return Uri.EscapeUriString(string.Format("{0}.{1}", this.FileName, this.Extension));
    }

    public async Task<Uri> UploadStreamToBlobAsync()
    {
        var blobPath = this.BlobPath();
        this.underlyingStream.Position = 0;
        var blob = this.blobContainer.GetBlockBlobReference(blobPath);
        await blob.UploadFromStreamAsync(this.underlyingStream);
        return blob.Uri;
    }
}
```

#### My Custom Provider

Using this custom Stream from within my own provider is simple.
When `ReadAsMultipartAsync` is called, it basically walks the form
elements and for each file calls `GetStream`.

```csharp
public override Stream GetStream(HttpContent parent, HttpContentHeaders headers)
{
    ContentDispositionHeaderValue contentDisposition = headers.ContentDisposition;
    if (contentDisposition != null)
    {
        // Found a file! Track it, and ultimately upload to blob store.
        if (!String.IsNullOrWhiteSpace(contentDisposition.FileName))
        {
            var fileInfo = new FileInfo(contentDisposition.FileName.Trim('"'));
            var blobStream = new MultipartBlobStream(this.imageBlobContainer, fileInfo.Name, fileInfo.Extension);
            this.FormFiles[fileInfo.Name] = blobStream;
            return blobStream;
        }
        else
        {
            return new MemoryStream();
        }
    }
    else
    {
        throw new InvalidOperationException("No 'Content-Disposition' header");
    }
}
```

Once processing is complete, `ExecutePostProcessingAsync` is called, and
I do my form field processing there.

```csharp
public override async Task ExecutePostProcessingAsync()
{
    foreach (var formContent in Contents)
    {
        ContentDispositionHeaderValue contentDisposition = formContent.Headers.ContentDisposition;
        // Not a file, treat as a form field.
        if (String.IsNullOrWhiteSpace(contentDisposition.FileName))
        {
            var fieldName = (contentDisposition.Name ?? "").Trim('"');
            var fieldValue = await formContent.ReadAsStringAsync();
            this.FormFields[fieldName] = fieldValue;
        }
    }
}
```

Finally, I've added a method `SaveAllAsync` to do the actual blob
uploads - this allows me to do any post-processing I want to do without
blocking the response to the client, and decouples the form processing
from the blob upload steps. It also allows me to store metadata about
the upload into Azure Table Storage. For the purposes of this blog
however, I've called that from within the controller.

```csharp
public async Task<IEnumerable<UploadedImage>> SaveAllAsync(string imageDescription)
{
    var tasks = new List<Task<UploadedImage>>();
    foreach (var blob in this.FormFiles.Values)
    {
        tasks.Add(Task.Run(async () =>
        {
            var blobUri = await blob.UploadStreamToBlobAsync();

            var upload = new UploadedImage()
            {
                PartitionKey = blob.FileName,
                RowKey = blob.Extension,
                FileName = blob.FileName,
                Extension = blob.Extension,
                BlobPath = blobUri.ToString(),
                UploadedOn = DateTime.UtcNow
            };
            var upsert = TableOperation.InsertOrReplace(upload);
            await this.imageDataTable.ExecuteAsync(upsert);

            return upload;
        }));
    }

    return await Task.WhenAll(tasks);
}
```

Putting It All Together
-----------------------

Once you've created these pieces, you need to use them from your code. I
wrote a simple HTML Form for uploading, and a simple ASP.Net controller
to do so. The form code is trivial:

```html
<h2>Upload File</h2>

@using (Html.BeginForm("upload", "api", FormMethod.Post, new { enctype = "multipart/form-data" }))
{
    <label>Image Description:</label> <input type="text" name="ImageDescription" value="Testing" /><br />
    <label>Image: </label> <input type="file" name="FileUpload1" /><br />
    <input type="submit" name="Submit" id="Submit" value="Upload" />
}
```

The controller is not much more complicated, and is a simple WebAPI
Controller at api/upload:

```csharp
public class UploadController : ApiController
{
    [Route("api/upload")]
    public async Task<IEnumerable<UploadedImage>> Post()
    {
        if (!Request.Content.IsMimeMultipartContent("form-data"))
        {
            throw new HttpResponseException(HttpStatusCode.UnsupportedMediaType);
        }

        var multipartStreamProvider = new AzureBlobMultipartProvider(
            await AzureUtilities.GetImageBlobContainerAsync("ImageDataConnectionString"),
            await AzureUtilities.GetImageDataTableAsync("ImageDataConnectionString"));
        var results = await Request.Content.ReadAsMultipartAsync<AzureBlobMultipartProvider>(multipartStreamProvider);
        var imageDescription = results.FormFields["ImageDescription"];

        return await results.SaveAllAsync(imageDescription);
    }
}
```

Next Steps
----------

I now have a form and controller capable of uploading images directly
into Azure Blob storage. There's nothing stopping me from adapting my
`MultipartBlobStream` to do processing of the image data before storing
it. In fact, in my application, I built several additional processors
into this step - one for downscaling the image to more useful
resolutions, another for storing subsamples of the image into multiple
blobs. Anything is possible here, as long as you're willing to take a
dependency on GDI+ or other low-level image stream processing libraries.

As always, I've made my code available [on GitHub as
asp-blob-uploader](https://github.com/noodlefrenzy/asp-blob-uploader)
under the MIT permissive license - feel free to fork, submit PRs, and
open issues as you see fit.

 

