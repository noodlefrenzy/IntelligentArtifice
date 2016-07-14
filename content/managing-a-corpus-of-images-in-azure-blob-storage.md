Title: Managing a Corpus of Images in Azure Blob Storage
Date: 2015-11-12 09:10
Author: noodlefrenzy
Category: Software
Tags: Azure, Azure Blob
Slug: managing-a-corpus-of-images-in-azure-blob-storage
Status: published

As mentioned in [my previous
post](http://www.mikelanzetta.com/2015/09/image-stream-processing-to-blob-storage/) I
was recently working on a project training [Deep
ConvNets](http://www.readcube.com/articles/10.1038%2Fnature14539?shared_access_token=DaxW8O-3gQoqte9kXFFUANRgN0jAjWel9jnR3ZoTv0PU8PImtLRceRBJ32CtadUBIC1dchyTLE3_1-FCJeTkHXnB0vI4SmupYf4v2t_dG6HjI9FdSJMFDQ6iWCA7T6tcte2-dAp-SzhLtuCkfPvhI6x--H5W98_7bqOVwSnqt1Vqo6bzZ5ZM7lCIPdavoThMMSXBgYmSjKSk0CrGtb5KUw%3D%3D)
for image recognition. As with any Machine Learning project one of the
primary things you need to make it successful is large amounts of data -
quality labeled data. With image-based convnets, though, the data are
images and metadata about those images, and in this post I'll go through
some of the design challenges I faced managing a large corpus of images
and how I solved them. As always the [code is up on
GitHub](https://github.com/noodlefrenzy/blob-collection-manager).

What Storage Do We Need?
------------------------

When training a domain-specific classifier (as I was) we need on the
order of hundreds of thousands to millions of images. In order to track
where they came from, whether we've transformed them in some way
(cropping, filtering, etc.), what models they've trained, and other
details we need some sort of metadata store.

For storing the images themselves Azure Blob Storage seemed like a
no-brainer. After all it's built for storing binary data like that,
gives us built-in fault tolerance and geo-replication, can easily be
fronted with a CDN - and when I screw things up I can easily delete the
container and start again.

Each "domain" would have its own container. The number of images and the
rate of change were sufficiently small that we didn't run into any
container-level throttling. In choosing the paths within the container,
I felt it was important to track three things: the suffix of the
original path, the "version" of the image, and whether this was the
original image or a transformed version. These choices have no impact on
the Blob Storage itself, but have a significant impact on how you think
about the images, so choose wisely. I wanted to keep all original images
"cloistered" so put `/original/` at the root of the path - you might
make a different call.

Choosing the metadata store is a bit more difficult as I have several
constraints to consider:

-   Fault-tolerance: We can't tolerate data loss, we can tolerate small
    outages but not significant downtime (so, roughly, CP on the [CAP
    triangle](https://en.wikipedia.org/wiki/CAP_theorem)).
-   Scale: We need to be able to scale to millions/tens-of-millions of
    records without significant performance degradation.
-   Queryability (yes, I know that's not a word): We're going to want to
    ask questions like "which images trained this model?" and "how many
    images with this label have been cropped"?
-   Flexibility: This is somewhat less important, but since when I
    started I wasn't quite sure what the metadata would look like it was
    important to be able to easily evolve and migrate the data.

Queryability rules out Azure Table Storage and other KV stores but that
still leaves a host of possible solutions. In the end I chose [SQL
Azure](https://azure.microsoft.com/en-us/services/sql-database/) with
[code-first Entity
Framework](http://weblogs.asp.net/scottgu/code-first-development-with-entity-framework-4).
This gave me the ability to quickly get up and running in both local
testing and production, the flexibility to change my model and have the
data come with me (via migrations), easy fault-tolerance, and a
reasonable approximation of scale. Scale was my biggest worry, but we
performed well even without query tuning or index-building - although if
I was taking this beyond the proof-of-concept level I'd have more
concrete numbers here and probably a few custom-built indexes to speed
things along.

Constructing the Metadata Model
-------------------------------

Coming up with what we wanted to track in the metadata was an iterative
process which made the [EF's
migration](https://msdn.microsoft.com/en-us/data/jj591621.aspx) ability
quite useful. The way I typically design (and then evolve) a data model
is to start with the goals. What does it need to know? What questions
does it need to answer? In our case, we needed to:

-   Store the locations of the images in blob storage
-   Version those images (so, e.g., we could get a new revision of the
    same library and still retain the existing revision if we'd already
    trained models on it)
-   Store information about a given image transform (pipeline) - the
    name, version, and in our case the command line

Equally important though was what we *did not need*:

-   We didn't care about individual images, only "sets" of them. This
    saved us tons of real-estate as tens of thousands of individual
    "`Image`" records could be condensed to a single "`ImageSet`".
-   We didn't care about parentage/inheritance. We originally had a
    model where an `Image` could be transformed via an
    `ImageTransform` and the resulting `Image` would store a link back
    to its parent. When switching to `ImageSets` we determined that we
    never actually used that information.

I've elided several elements of our actual data-model related to
tracking how images get combined into training sets then coupled with
neural nets to form trained neural nets. They are immaterial to the task
of managing corpora of images but might show up in a subsequent post.

The resulting model is actually simple enough to store in **Azure Table
Storage** since we don't really need the queryability, so the code up on
GitHub uses `TableEntities` to track the data rather than code-first. I
felt this would make it easier for people to adopt since they now just
need a single Azure Storage stamp instead of having to stand up a SQL
Azure instance. If and when I do a subsequent post with NN-specific
details the EF code will come with it.

The resulting data model is simply (note the string math for creating
the blob path as described above):

```csharp
public class ImageSet : TableEntity
{
    public ImageSet() { }

    /// <summary>
    /// Set of (possibly transformed) images.
    /// </summary>
    /// <remarks>
    /// Blob path is original/_dir_/_image version_, or if transformed it's transform/_transform name_/_transform version_/_dir_/_image version_
    /// </remarks>
    public ImageSet(string pathSuffix, string version, ImageTransform transform = null)
    {
        if (pathSuffix == null) throw new ArgumentNullException("pathSuffix");
        var prefix = transform == null ? "original/" : string.Format("transform/{0}/{1}/", transform.Name, transform.Version);
        this.BlobPath = prefix + pathSuffix.Replace('\\', '/') + "/" + version;

        this.Path = pathSuffix == "" ? "<root>" : pathSuffix;
        this.Version = version;
        this.Tags = new List<string>();

        this.PartitionKey = this.CleanPartitionKey(this.Path);
        this.RowKey = this.CleanRowKey(this.Version);

        if (transform != null)
        {
            this.TransformPartitionKey = transform.PartitionKey;
            this.TransformRowKey = transform.RowKey;
        }
    }

    public string Path { get; set; }

    public string Version { get; set; }

    public List<string> Tags { get; set; }

    public string BlobPath { get; set; }

    /// <summary>
    /// If the images have been transformed, store the PK/RK of the transform pipeline.
    /// </summary>
    public string TransformPartitionKey { get; set; }
    public string TransformRowKey { get; set; }
}

public class ImageTransform : TableEntity
{
    public ImageTransform() { }

    public ImageTransform(string name, string version)
    {
        this.Name = name;
        this.Version = version;

        this.PartitionKey = this.CleanPartitionKey(this.Name);
        this.RowKey = this.CleanRowKey(this.Version);
    }

    public string Name { get; set; }

    public string Version { get; set; }

    public string CommandLineArguments { get; set; }
}
```

Uploading Local Image Libraries
-------------------------------

One of the hurdles we faced was in uploading large sets of images to
blob storage. We would get "drops" of tens of thousands of images and
would need to upload them to blob storage, where we could then fire up
servers to transform, slice and dice them to the millions we needed.
This upload process, however infrequent, was a bottleneck, so we spent a
bit of time trying to improve it.

My goal was to make sure that we could upload multiple images
concurrently, but that we were able to throttle this upload process to
prevent over-saturating network bandwidth or triggering any quota issues
on the Azure (unlikely) or Comcast (much more likely) side.

Often, the libraries we were given were a collection of directories like
"`red/angry/robin`" where each component of the directory could be
considered a "tag". For ML purposes, we would later combine those tags
into individual labels for training. First, I needed to find all of the
images in each subdirectory of the root to the library I'd been given.
Assuming `this.Extensions` contains a list of image extensions I'm
looking for:

```csharp
// Give me all of the images...
var images = from file in Directory.EnumerateFiles(rootDirectory, "*.*", SearchOption.AllDirectories).Select(x => new FileInfo(x))
             where this.Extensions.Contains(file.Extension)
             select file;

// Grouped by directory
var byDirectory = from img in images
                  group img by img.DirectoryName;
```

will give us all images by directory as lazily instantiated lists.
Turning the `EnumerateFiles` results into `FileInfo` classes not only
allows us to easily filter on extension and group by directory, but
makes building blob paths easier later on.

We can then walk the directories, turning their paths into lists of
tags, uploading the images inside and storing the `ImageSet` metadata:

```csharp
var uploadTasks = Enumerable.Empty<Tuple<FileInfo, Task>>();
var imgSets = new List<ImageSet>();
foreach (var dir in byDirectory)
{
    var suffix = dir.Key.Length == rootDirectory.Length ? "" : dir.Key.Substring(rootDirectory.Length + 1);
    suffix = suffix.Trim();
    var imgSet = new ImageSet(suffix, imagesVersion)
    {
        Tags = this.TagExtractor(suffix).Select(x => x.Trim()).Where(x => !string.IsNullOrEmpty(x)).ToList()
    };

    uploadTasks = uploadTasks.Concat(dir.Select(file => 
        Tuple.Create(file, this.BlobUploader(file.FullName, imgSet.BlobPath))));
    imgSets.Add(imgSet);
}
```

Note the mix of LINQ and regular imperative loops (e.g. foreach) here.
My goal is clarity, not "Haskell-ness", and a foreach loop made the
"what are we doing for each directory" code much cleaner. I store each
upload task with the associated file as a Tuple, allowing me to easily
track failures back to the file that failed.

The most important piece of the code above, however, is that the
uploadTasks is an enumerable based on `Concat'd` `Selects` so is lazily
evaluated. This allows the following code:

```csharp
var failedUpserts = await Utilities.ThrottleWork(MaxParallelUpserts, imgSets.Select(imgSet => this.ImageSetUpserter(imgSet)));
var failedUploads = await Utilities.ThrottleWork(MaxParallelUploads, uploadTasks.Select(x => x.Item2));
```

to effectively throttle the number of concurrent operations.
`ThrottleWork` takes a number of tasks to run concurrently and an
enumerable of those tasks and ensures that the next task is not
"comprehended" until a previous one has finished. Failing tasks are
tracked and returned once all tasks complete.

```csharp
public static async Task<IEnumerable<Task>> ThrottleWork(int maxWork, IEnumerable<Task> tasks)
{
    var working = new List<Task>(maxWork);
    var failures = new List<Task>();
    foreach (var task in tasks)
    {
        if (working.Count == maxWork)
        {
            var completed = await Task.WhenAny(working);
            working.Remove(completed);
            if (completed.Status != TaskStatus.RanToCompletion)
                failures.Add(completed);
        }
        working.Add(task);
    }
    await Task.WhenAll(working);
    foreach (var task in working)
    {
        if (task.IsFaulted) failures.Add(task);
    }

    return failures;
}
```

The actual [uploading of
blobs](https://github.com/noodlefrenzy/blob-collection-manager/blob/master/ImageBlobData/Utilities.cs#L63)
and
[upserting](https://github.com/noodlefrenzy/blob-collection-manager/blob/master/BlobCollectionManager/Program.cs#L51)of
`ImageSets` are fairly simple and are in the code on GitHub.

Conclusion
----------

Hopefully this outlined some of the challenges with working with large
binary datasets. I've tried to cover how I made decisions on where to
store information and how to build data models for it. I've also tried
to outline how one would throttle existing workloads to avoid
over-saturating restricted resources using simple C\# LINQ-based
solutions. I didn't cover the [transformation
pipeline](https://github.com/noodlefrenzy/blob-collection-manager/blob/master/BlobCollectionManager/ImageDirectoryCrawler.cs#L95)
as that was simply using ImageMagick and forking processes - there are
much better ways of doing that work and nothing there was innovative
enough for calling out, but once again the code is on GitHub.

I'd love any comments, suggestions, or improvements - either on this
post or via
[GitHub](https://github.com/noodlefrenzy/blob-collection-manager).
Committers are always welcome as are questions and issues. I'll try and
follow this up with additional work in this area so you can see the
Entity Framework version but let me know if there are other aspects
you'd like to see.

 

