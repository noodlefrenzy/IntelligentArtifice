Title: Real-time Mapping with SignalR and Event Hubs
Date: 2015-08-18 10:20
Author: noodlefrenzy
Category: Software
Tags: .NET, C#, EventHub, Geo, WebSockets
Slug: real-time-mapping-with-signalr-and-event-hubs
Status: published

One of my recent projects had to do with watching people moving around
the city - not in a creepy stalker way, but trying to get some sense of
where people congregated and general walking traffic flow. As anyone who
has dealt with large data, especially large geo data can tell you -
visualization is everything. Somehow looking at a screen full of
lat/long coordinates and timestamps just doesn't tell you a story like
seeing things play out on the
map.

[![route\_animation]({filename}/images/route_animation.gif)]({filename}/images/route_animation.gif)

So what if you have large amounts of geo data coming in from different
users, say via a high-scale queuing mechanism like Event Hubs? What if
you want to display that to anyone who wants to see it, in
near-real-time? I decided to use [Leaflet](http://leafletjs.com/)(a
great open-source JS mapping package ([book](http://amzn.to/1J4LHxd)))
and [SignalR](http://signalr.net/)(a great open-source
[WebSockets](http://amzn.to/1J4LKZW)package for ASP.Net
([book](http://amzn.to/1HLx29i))) to make that happen. As always, I've
released all of my code [on
GitHub](https://github.com/noodlefrenzy/asp-mappy), and I'll walk you
through the steps needed to make this scenario happen.

Mapping with Leaflet.js
-----------------------

Let's start at the front - how can I show a map on the screen? There are
a ton of libraries out there - for apps, full desktop applications, and
websites. Let's assume we're going to be building a website, and want a
Javascript solution. Even there, we have many options - from our own
Bing Maps to Google Maps or even MapQuest. However, I like
[Leaflet.js](http://leafletjs.com/) for a few reasons - first, they have
an easy to use and [well](http://leafletjs.com/reference.html)
[documented](http://leafletjs.com/examples.html)API; second, they can
work with a variety of different tile-sets, so you can develop on
OpenMaps and then later swap your look-and-feel for a more Bing Maps
style with a one line code change.

Integrating Leaflet into your code is as simple as including their CSS
and Javascript, which I've done via their CDN links:

```html
<head>
...
    <link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.css" />
...
</head>
<body>
...
    <script src="http://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.3/leaflet.js"></script>
...
</body>
```

I chose to put it into `_Layout.cshtml` since this was the crux of my
site. To use Leaflet, I picked a center-point and zoom level for my map,
added a well-named `div`, picked a size for it, and created a map:

```html
// from site.css:
#map { height: 500px; }

// from _Home.cshtml:
<!-- ko with: home -->
<div class="container">
    <h2>Mappy</h2>
</div>
<div class="container">
        ...
        <div class="col-md-8">
            <div id="map"></div>
        </div>
    </div>
</div>
<!-- /ko -->

// from Index.cshtml:
<script>
    var centerLat = @ViewBag.CenterLatitude;
    var centerLon = @ViewBag.CenterLongitude;
    var zoom = 13;
    var map = L.map('map').setView([centerLat, centerLon], zoom);
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>[…]',
        maxZoom: 18,
        id: '@ViewBag.MapsId',
        accessToken: '@ViewBag.MapsAccessToken'
    }).addTo(map);
...
```

Note the highlighted lines where I pull constants from the ViewBag -
this allows me to factor out my maps app ID and access token, as well as
the center-point for my map.

Real-time Geo Data with SignalR
-------------------------------

#### SignalR Server-Side

Integrating SignalR isn't much more difficult than Leaflet.js, but it
has to integrate at two different layers of the stack since it's the
bridge between them. Including it in your ASP.Net application is done as
you would expect - Install the `Microsoft.AspNet.SignalR` NuGet package.
Once that's installed you'll need to decide how you want to use it
to send data from server to clients - I've used [SignalR
Hubs](http://www.asp.net/signalr/overview/guide-to-the-api/hubs-api-guide-javascript-client)in
this example, as it allowed me to create different hubs for different
purposes (although I'm only using one in this example code).

Creating a Hub is as simple as creating a class inheriting from the
appropriate `Hub` class and implementing a few methods. Behind the
scenes it creates the appropriate proxies and lets you do your client
wiring from there. The server-side needs to get the hub context instance
and then use that to send data to clients, while the hub uses its
internal Clients.All dynamic collection to deliver that data. I use a
simple static method on my Hub to allow server-side code to find the hub
context from the global connection, making calling code trivial to
implement. As a result, the Hub code looks like:

```csharp
public class RouteHub : Hub
{
    public RouteHub()
    {
    }

    public static IHubContext Hub()
    {
        return GlobalHost.ConnectionManager.GetHubContext<RouteHub>();
    }

    public static void Send(IHubContext hub, string userId, float lat, float lon)
    {
        hub.Clients.All.newPoint(userId, lat, lon);
    }

    public void Send(string userId, float lat, float lon)
    {
        Clients.All.newPoint(userId, lat, lon);
    }
}
```

Note the `Clients.All.newPoint()` call - newPoint is a `dynamic` method
which gets wired into the created proxy and passed through to the
client, as you'll see below. Calling the hub from the server is as easy
as:

```csharp
RouteHub.Send(RouteHub.Hub(), pt.UserID, (float)pt.Latitude, (float)pt.Longitude)
```

One thing to notice is that I'm casting the `doubles` I have internally
for lat/lon into `floats` when passing them down the wire. SignalR seems
to have trouble passing `doubles` through to Javascript - possibly
because the language doesn't support them - limiting it to `floats`
fixes the problem. Now that we have the hub created, we just need to
start SignalR itself when we start up our website - we do this in the
Startup.cs code with the addition of a single line:

```csharp
public partial class Startup
{
    public void Configuration(IAppBuilder app)
    {
        app.MapSignalR();
    }
}
```

#### Wiring the SignalR Client

Now that we have a server which can send us data, we need to wire up the
client to receive it. Wiring SignalR in the client requires
three modifications. First - include the hubs, allowing the client code
to talk to the proxies. Second - create a handler to process
incoming messages from the hub you're listening to. Finally - start
listening. This is actually a pretty small chunk of code, as you can see
here:

```html
<script src="~/Scripts/jquery.signalR-2.2.0.min.js"></script>
<script src="~/signalr/hubs"></script>
<script>
    $(function () {
        var routeHub = $.connection.routeHub;
        routeHub.client.newPoint = function (userid, lat, lon) {
            // Do something exciting!
        };

        $.connection.hub.start().done(function () {
        });
    });
</script>
```

Note the reappearance of the `newPoint` method - this must correspond
with the dynamic method you're calling from within the Hub above (via
`Clients.All`).

Geo Data and Event Hub
----------------------

So now I have a client-server connection, and a map. Let's see if I
can't send some data to that map! Since I'm planning on having hundreds
or thousands of users sending me geo data, and I'm going to want to use
this geo data for more than just mapping, [Event
Hubs](http://azure.microsoft.com/en-us/services/event-hubs/) seems like
a natural mechanism to decouple the senders from the receivers. The one
caveat with writing a receiver for Event Hubs is that they have to
manage their own state (context) so they can pick up where they left
off. I'll be using the Azure-provided `EventProcessorHost` library to do
that work for me - it stores offset data for each partition in Azure
Blob storage and uses blob leases for ad-hoc load balancing, so is quite
a useful little piece of code, and is simple to set up. You just NuGet
install Microsoft.Azure.ServiceBus.EventProcessorHost, and then
implement and instantiate your event processor. I've chosen to
use/assume JSON serialization via Newtonsoft's Json.NET, and my data
payload class looks like:

```csharp
public class RoutePointEH : IRoutePoint
{
    public double Latitude { get; set; }
    public double Longitude { get; set; }
    public string UserID { get; set; }
    public DateTime MeasurementTime { get; set; }
    public DateTime Timestamp { get; set; }
}
```

(I'll come back to the reason for the `IRoutePoint` interface), while
the resulting EventProcessor looks like:

```csharp
public class RoutePointProcessorFactory : IEventProcessorFactory
{
    public RoutePointProcessorFactory(Action<IRoutePoint> onItem)
    {
        this.onItemCB = onItem;
    }

    public IEventProcessor CreateEventProcessor(PartitionContext context)
    {
        return new RoutePointProcessor(this.onItemCB);
    }

    private Action<IRoutePoint> onItemCB;
}

public class RoutePointProcessor : IEventProcessor
{
    public RoutePointProcessor(Action<IRoutePoint> onItem)
    {
        this.onItemCB = onItem;
    }

    private Action<IRoutePoint> onItemCB;

    public Task CloseAsync(PartitionContext context, CloseReason reason)
    {
        return Task.FromResult(false);
    }

    public Task OpenAsync(PartitionContext context)
    {
        return Task.FromResult(false);
    }

    public async Task ProcessEventsAsync(PartitionContext context, IEnumerable<EventData> messages)
    {
        foreach (var message in messages)
        {
            var routeItem = AzureUtilities.DeserializeMessage<RoutePointEH>(message);
            this.onItemCB(routeItem);
            if (this.ShouldCheckpoint())
                await context.CheckpointAsync();
        }
    }
}
```

and is created and registered using a simple utility method:

```csharp
public static async Task<EventProcessorHost> AttachProcessorForHub(
    string processorName, 
    string serviceBusConnectionString,
    string offsetStorageConnectionString,
    string eventHubName,
    string consumerGroupName,
    IEventProcessorFactory processorFactory)
{
    var eventProcessorHost = new EventProcessorHost(processorName, eventHubName, consumerGroupName, serviceBusConnectionString, offsetStorageConnectionString);
    await eventProcessorHost.RegisterEventProcessorFactoryAsync(processorFactory);

    return eventProcessorHost;
}
```

Note that it creates the generic EventProcessorHost class with the Event
Hub details, and then hands it a factory to create processors for each
partition. Each partition processor then is responsible for saving its
own checkpoint at an interval of its choosing (factored into the
unshown `ShouldCheckpoint` method).

I then create an additional wrapper class as a "point source" which
takes in a callback for what to do when new points come in and wires
everything up, allowing me to factor out all of the code for pulling
configuration values and creating the factory/processor, and even
letting me swap out Event Hubs for other "point sources" like
canned/random data or even Azure Table Storage (see [the
repo](https://github.com/noodlefrenzy/asp-mappy/blob/master/MappyData/RoutePointSource.cs)
for details).

```csharp
public class EventHubRoutePointSource
{
    public EventHubRoutePointSource(Action<IRoutePoint> onNewPoint)
    {
        this._onPoint = onNewPoint;
    }

    public async Task StartAsync()
    {
        var ehConnStr = ...;
        var storageConnStr = ...;
        var eventHubName = ...;
        var consumerGroup = ...;

        var factory = new RoutePointProcessorFactory(this._onPoint);

        await AzureUtilities.AttachProcessorForHub("mappy", ehConnStr, storageConnStr, eventHubName, consumerGroup, factory);
    }

    private Action<IRoutePoint> _onPoint;
}
```

Wiring It All Together
----------------------

Now that I have all of the pieces, how do I wire it all together? First,
in `Global.asax.cs` we add a single line to start our chosen "point
source" and drive its incoming data into our SignalR hub:

```csharp
RoutePointSourceFactory.StartAsync(AzureUtilities.FromConfiguration("RoutePointSource"), 
    pt => RouteHub.Send(RouteHub.Hub(), pt.UserID, (float)pt.Latitude, (float)pt.Longitude));
```

Then in our client's "do something exciting!" section, we wire it up to
write this incoming geo data onto our map, with each user getting its
own path layer (a polyline) and "walking man" marker at the front.

```js
var paths = {};
var pathMarkers = {};

$(function () {
    var iconUri = '/Content/Sports-Walking-icon-white.png';
    var endIcon = L.icon({ iconSize: [38, 38], iconAnchor: [12, 12], iconUrl: iconUri });

    var routeHub = $.connection.routeHub;
    routeHub.client.newPoint = function (userid, lat, lon) {
        if (paths[userid]) {
            paths[userid].addLatLng([lat, lon]);
            if (pathMarkers[userid]) map.removeLayer(pathMarkers[userid]);
            pathMarkers[userid] = L.marker([lat, lon], { icon: endIcon }).addTo(map);
        } else {
            paths[userid] = L.polyline([[lat, lon]], { color: 'red', weight: 5 }).addTo(map);
            pathMarkers[userid] = L.marker([lat, lon], { icon: endIcon }).addTo(map);
        }
    };

    $.connection.hub.start().done(function () {
    });
});
```

What Next?
----------

If you've been following along in the repo, you'll notice that the code
above is different than what is up there - that's simply due to space
constraints, this post is already in TL;DR territory and any more
features would only make that worse. The main differences between what's
here and what's in [the repo](https://github.com/noodlefrenzy/asp-mappy)
are:

-   I've factored out the "point source" into three distinct sources -
    an Event Hub source as outlined here, an Azure Table Storage source,
    and a "Random" source with initial points pulled from a neighborhood
    around the center and then a random walk from there.
-   I've integrated the
    fantastic [Chroma.js](https://github.com/gka/chroma.js/) to ensure
    each path gets a unique random yet pleasing color, and made an LRU
    to limit the total number of paths I show on-screen.
-   I've integrated the remarkably easy-to-use
    [Leaflet.heat](https://github.com/Leaflet/Leaflet.heat) to add a
    heatmap layer for each user, showing how individuals walk and where
    there "hot spots" might be.
-   I've created a simple CLI program to drive random data into the
    Event Hub, allowing easy testing.

I hope I've showed you that getting a mapping web application up and
running is actually pretty easy, and integrating near-real-time data can
be done with little code using Event Hubs and SignalR. As always, my
code is [up on GitHub](https://github.com/noodlefrenzy/asp-mappy)and is
MIT license, so do with it what you will. Let me know via comments,
twitter, or GitHub issues if you have any feedback - I'd love to hear
it.

