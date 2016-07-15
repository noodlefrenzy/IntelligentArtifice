Title: Using Project Oxford To Pull Entities From Images
Date: 2015-05-14 11:06
Author: noodlefrenzy
Category: Software
Tags: C#, Entity Extraction, Machine Learning, ML, MSR, OCR, Project Oxford
Slug: using-project-oxford-to-pull-entities-from-images
Status: published

I love my job. Less than a week after watching the amazing announcements
at [//Build2015](http://www.buildwindows.com/), I had a chance to try
using some of them on a real project as part of a hackathon.
Unfortunately, I can't share the actual problem they are trying to
solve, but the work itself is another matter. Consider images containing
some interesting, structured text and imagine turning them into a rich
model of intent and the entities involved using OCR and Intent/Entity
Extraction. I know I could build such a solution, but it would take me a
long time. Finding the right OCR library and integrating it, and then
finding/building an Entity Extractor and tuning it - it'd be a major
nightmare.

[Project Oxford](https://www.projectoxford.ai/)([video
here](http://channel9.msdn.com/Events/Build/2015/2-613)) is a new suite
of Machine Learning libraries from MSR exposed as Azure Marketplace
APIs.  It differs from Azure ML in that these are pre-trained/pre-built
libraries for specific but common ML tasks that are, in many cases,
already part of various backend services in Microsoft (Bing, OneDrive,
Cortana, etc.). Their [Vision
API](https://www.projectoxford.ai/vision)contains an OCR module exposed
as a simple RESTful endpoint, and they have a system named
[LUIS](https://www.projectoxford.ai/luis)for training and deploying
intent and entity recognition models that can be just as robust as
Cortana. These two pieces turn this near impossible task (certainly
impossible during a hackathon) into something achievable, so I thought
I'd walk you through the code I wrote to do just that. All of the code
in this post is [published on
GitHub](https://github.com/noodlefrenzy/image-to-entities)under MIT
license, but probably not quite as terse (I've removed braces from
single statements etc. to mitigate TL;DR syndrome).

The Input
---------

![Morpheus: What if I told you it was staring you right in the face?]({filename}/images/1wL61Ro1.jpg)

So what sort of input data should we use? It needs to be images with
structured text, and the text should have both an overall
intent/category as well as individual entities within it. Where could we
find something like that...

Ohhh, that's right! The internet is covered in the damn things! We could
get a training set in the millions just by squatting on Reddit or 4chan.
Settled - we'll try and pull text from memes and determine "intent"
(which meme are we looking at?) and "entities" (what is Morpheus telling
us?). How do we get started? We'll start out with the Morpheus image and
go from there - first off by getting our marketplace accounts set up. Go
and sign up for the [Vision
API](http://azure.microsoft.com/en-us/marketplace/partners/visionapis/visionapis/) and
get on the waiting list for [LUIS](https://www.luis.ai/?ref=1699313) -
you'll need to wait until LUIS lets you in before you can get this code
completely running, but the turnaround time has been pretty good.

Extracting Text
---------------

Let's use the Vision APIs to extract text from our memes. We could use
the SDK that they provide, but since (a) they don't have a Nuget package
and (b) I might want to rewrite in Node.js or Python later, let's stick
with the raw REST API. I'll create an `ImageToText` class to keep track
of the API key and the URI format, and build a method to fetch OCR
results by passing in the image URI:

```csharp
public ImageToText(string apiKey)
{
  this.apiKey = apiKey;
}

private readonly string apiKey;
private const string OCRURIFormat = "https://api.projectoxford.ai/vision/v1/ocr?language={0}&detectOrientation={1}";
private const string DefaultLanguage = "unk";
private const bool DefaultDetectOrientation = true;
private const string APIKeyHeader = "Ocp-Apim-Subscription-Key";

public async Task<JObject> ProcessImageToTextAsync(Uri imageUri, string language = DefaultLanguage, bool detectOrientation = DefaultDetectOrientation)
{
  var requestBody = new JObject();
  requestBody["Url"] = imageUri.ToString();

  var ocrUri = string.Format(OCRURIFormat, language, detectOrientation);
  var request = WebRequest.Create(ocrUri);
  request.ContentType = "application/json";
  request.Method = "POST";
  request.Headers.Add(APIKeyHeader, this.apiKey);

  using (var requestStream = await request.GetRequestStreamAsync().ConfigureAwait(false))
  {
    var bodyBytes = Encoding.UTF8.GetBytes(requestBody.ToString());
    await requestStream.WriteAsync(bodyBytes, 0, bodyBytes.Length).ConfigureAwait(false);
  }

  // Since errors from this API typically come back with a JSON payload describing the problem, trap WebExceptions and pull the response anyway.
  HttpWebResponse response;
  try {
    response = (HttpWebResponse)(await request.GetResponseAsync().ConfigureAwait(false));
  } catch (WebException we) {
    response = (HttpWebResponse)we.Response;
  }

  JObject responseJson;
  using (var responseStream = new StreamReader(response.GetResponseStream()))
  {
    var responseStr = await responseStream.ReadToEndAsync().ConfigureAwait(false);
    responseJson = JObject.Parse(responseStr); // I'm fine throwing a parse error here.
  }

  if (response.StatusCode == HttpStatusCode.OK) // Could probably relax this to "non-failing" codes.
    return responseJson;
  else
    throw new Exception(string.Format("Failed call: {0} failed to OCR - code {1} - details\n{2}", 
      imageUri, response.StatusCode, responseJson.ToString(Newtonsoft.Json.Formatting.Indented)));
}
```

That seems like a lot of code but much of it is just boilerplate HTTP
request/response cycle - let's walk through it. The constructor takes
and squirrels away the API key, and the class defines a few constants
including the format of the REST URI, leaving the method by default just
taking in a URI for the image and assuming that it should try and
auto-detect language and orientation. The method itself builds a POST
request containing the image Url in a JSON payload and funnels it off to
the server, awaiting a response. When there's an error in the method
invocation on the server side, it often sends back a JSON payload
containing the error details, so we trap `WebException` and try to pull
out those details. Finally, we read the response stream into a string
and attempt to parse it as JSON, returning a `JObject` as a result. We
could easily create a POCO to deserialize into, but ... I didn't want to
bother. Note how all of the async calls end
in `.ConfigureAwait(false)` - this is because we're in library code and
want to allow this to be called from e.g. UI threads without
self-deadlocking (a [StackOverflow
thread](http://stackoverflow.com/questions/13489065/best-practice-to-call-configureawait-for-all-server-side-code)
and [great
post](http://www.tugberkugurlu.com/archive/the-perfect-recipe-to-shoot-yourself-in-the-foot-ending-up-with-a-deadlock-using-the-c-sharp-5-0-asynchronous-language-features)on
the issue, for those unfamiliar).

Parsing Words Into Lines
------------------------

The `JObject` we give back from the call contains a hierarchy of
information (outlined in [the
docs](https://dev.projectoxford.ai/docs/services/54ef139a49c3f70a50e79b7d/operations/5527970549c3f723cc5363e4))
with `regions` containing one or more `lines` containing one or
more `words`. Our goal for meme text is to pull all of the text into a
single string, which I do using the following:

```csharp
public static string ExtractTextFromResponse(JObject responseJson)
{
  return string.Join(" ", from r in responseJson["regions"]
                          from l in r["lines"]
                          from w in l["words"]
                          select (string)w["text"]);
}
```

Joining all of the words' text together for all lines in all
regions. Let's take a look at the results.

Results... and a Realization
----------------------------

![Stuff]({filename}/images/5ocZvsW1.jpg)

So running the OCR on our example image above, I notice a problem - it's
missed a chunk of text and returned "what if it was staring you right in
the face?". Crap, well at least the text it did find it got right.
Boromir is right - of course Oxford trolls me and pulls "one *does*
simply ocr text from an image"!

In retrospect, I should have expected a problem - we're using technology
meant to pull words from objects in the image, to pull words that have
been overlaid on an existing image. It's a whole different training
base, and the words in memes appear totally different than the words in
reality. Perhaps we can transform them in some way to pull text
correctly - maybe pull a single color channel or invert.

I've tried a bunch of different examples of simple filters, and so far
pulling out the blue channel or bumping gamma to \~2.5 seems to work
reasonably well. I'll publish a future post with some of the work I did
here - if you're curious now, see [the GitHub
repository](https://github.com/noodlefrenzy/image-to-entities). There's
more work that can be done here - for instance, I believe a pre-filter
doing edge detection would work well - but let's move on to LUIS.

Training an Entity Extractor
----------------------------

Now we can work with LUIS from Project Oxford to train a model for
recognizing the type of meme and the contents within. We first log into
LUIS (you did request an invite earlier, right?) and create a new
application. We can then create a few intents and entities, and start
adding "utterances" - for each utterance you pick an intent and then
label any entities within it. You can then re-train the model with the
button in the bottom left and see how it did - here's a shot of what my
model looks like after a few training utterances have been added:

[![LUIS\_Training]({filename}/images/luis_training.png)]({filename}/images/luis_training.png)

Now that it's trained, you can go back to your application list and hit
"Publish":

[![LUIS\_Publish]({filename}/images/LUIS_Publish.png)]({filename}/images/LUIS_Publish.png)

Once it's published, you can just invoke it with the given URL and the
utterance you want it to try and tag. For the Boromir example above,
I've run it through the single-channel filter (blue) and then passed it
into the model:

```csharp
var mordorImage = "http://i.imgur.com/5ocZvsW.jpg";
var imageToText = new ImageToText(visionApiKey);
var result = await imageToText.ProcessImageToTextAsync(await ImageUtilities.SingleChannelAsync(new Uri(mordorImage), ImageUtilities.Channel.Blue));
var lines = ImageToText.ExtractLinesFromResponse(result).ToList();
lines.RemoveAt(lines.Count - 1); // Remove memegenerator.net line.
var text = string.Join(" ", lines);

var luis = new TextToEntitiesAndIntent(luisApp, luisApiKey);
var luisResult = await luis.DetectEntitiesAndIntentFromText(text);
Trace.TraceInformation(luisResult.ToString(Newtonsoft.Json.Formatting.Indented));
```

When I do, it comes out with

```js
{
  "entities": [
    {
      "entity": "ocr some text from an image",
      "type": "Subject1"
    }
  ],
  "intents": [
    {
      "intent": "Mordor",
      "score": 0.9998174
    },
    ...
  ]
}
```

As you can see, it pulled the right meme type *and* entity from the meme
text. Not too surprising since I've over-fit the model, but it gives you
some ideas of how you can string Oxford, LUIS, and some simple image
processing together to build a pipeline. Once again, all of this code is
[on GitHub](https://github.com/noodlefrenzy/image-to-entities) under and
MIT license, so feel free to use it as you see fit.

