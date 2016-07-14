Title: Talking to EventHub from Node
Date: 2014-09-28 13:14
Author: noodlefrenzy
Category: Software
Tags: Azure, EventHub, Node
Slug: talking-to-eventhub-from-node
Status: published

This past week, I participated in a hackfest trying to get some
[Alljoyn](https://www.alljoyn.org/) devices talking to
[Nitrogen](http://nitrogen.io/).  It was a great time, getting to learn
some new technologies, get exposed to the ~~pain ~~wonder of working
with IoT hardware, and watch my bosses ([John
Shewchuk](http://blogs.msdn.com/b/johnshews_blog/) and [Tracey
Trewin](http://channel9.msdn.com/Events/Visual-Studio/Visual-Studio-Live/Tracey-Trewin-Architecture-Intellitrace-DevOps-Unit-Testing))
sling some code.  My goal was to have Nitrogen write device telemetry
data to [Azure
EventHub](http://azure.microsoft.com/en-us/services/event-hubs/), and
potentially have other Node or C\# workers process the telemetry across
devices.

To that end, I downloaded the Azure Node SDK and went to connect to my
hub - at that point I realized I had a problem, the Node SDK hasn't been
extended to talk to EventHub yet!  I looked around, and perhaps my
bingle-fu is weak but I didn't see any existing unofficial Node
packages, so I decided I'd write one myself.

First, I took a look at the .NET API, figuring I'd just copy that - no
dice, as that client uses magic to send messages, creating the client
based on the connection string in the app's config:

```csharp
var eventHubClient = EventHubClient.Create("hubName");
```

or using the Shared Access Signature Token created via a different form
of magic:

```csharp
var serviceUri = ServiceBusEnvironment.CreateServiceUri(
      "https", namespace, 
      string.Format("{0}/publishers/{1}/messages", hub, publisher))
  .ToString()
  .Trim('/');
var token = SharedAccessSignatureTokenProvider.GetSharedAccessSignature(
      sasKeyName, sasKeyValue, 
      serviceUri, tokenTTL);
```

Neither of these methods exist in the Azure Node SDK, so I was forced to
seek farther afield.

#### Creating a Token and Sending RESTfully

With the help of a [great
post](http://developers.de/blogs/damir_dobric/archive/2013/10/17/how-to-create-shared-access-signature-for-service-bus.aspx)
by Damir Dobric, I was able to convert his code into a Node-ful way of
doing things, then use the [EventHub REST
API](http://msdn.microsoft.com/en-us/library/azure/dn790664.aspx) to
send messages to my very own Event Hub.  I created a custom SAS key for
sending using the portal:

[![Creating
Alternate SAS
Keys](http://www.mikelanzetta.com/wp-content/uploads/2014/09/eventhub_saskeys.png)](http://www.mikelanzetta.com/wp-content/uploads/2014/09/eventhub_saskeys.png)

used my new code to build a token from them:

```js
function createSharedAccessToken(namespace, hubName, saName, saKey) {
    if (!namespace || !hubName || !saName || !saKey) {
        throw "Missing required parameter";
    }

    var uri = 'https://' + namespace +
        '.servicebus.windows.net/' + hubName + '/';

    var encoded = encodeURIComponent(uri);
    
    var epoch = new Date(1970, 1, 1, 0, 0, 0, 0);
    var now = new Date();
    var year = 365 * 24 * 60 * 60;
    var ttl = ((now.getTime() - epoch.getTime()) / 1000) + (year * 5);

    var signature = encoded + '\n' + ttl;
    var signatureUTF8 = utf8.encode(signature);
    var hash = crypto.createHmac('sha256', saKey).update(signatureUTF8).digest('base64');

    return 'SharedAccessSignature sr=' + encoded + '&sig=' + 
        encodeURIComponent(hash) + '&se=' + ttl + '&skn=' + saName;
}
```

and sent the message.  I've [open-sourced this code on
GitHub](https://github.com/noodlefrenzy/event-hub-client), please feel
free to use it (Apache v2 licensed), and pull requests are always
welcome.  Now I just needed to hook up the receive API and I'd be all
set!

*This is where things really went sideways.*

For the receive piece, EventHub only supports AMQP - specifically AMQP
1.0.  I've been looking through the various Nodejs packages, and haven't
found anything I can use to talk AMQP 1.0.  For `amqp.node` and `node-amqp`,
they only support 0.9.1 and I don't see 1.0 support pending or in
anyone's forks.  The node-qpid package seems promising, as it's based on
Apache Qpid Proton which does support 1.0, but the package is a native
code package that requires you to have Proton 0.3 installed, and I can't
get that to build on Windows at this point.  I've started porting
the node-qpid package to Proton 0.7 (the latest), but I'm running into
linker errors.

At this point, it has gone beyond a slight investigation for a hackfest
and into something more serious.  I'm starting to talk with the EventHub
team about their release schedule, and I'm looking for insight from the
community as to whether they'd like one of the non-native-code packages
(amqp.node or node-amqp) updated to 1.0, or whether they'd want
node-qpid upgraded to 0.7 - I only have time to work on so much.  At
this point, my inclination is to upgrade amqp.node, but suggestions and
advice are always welcome.

#### PostScript

Link to event-hub-client, my start on a Nodejs REST-based EventHub
client: <https://github.com/noodlefrenzy/event-hub-client>, now
published in the `npm` registry
at <https://www.npmjs.org/package/event-hub-client>.

Also, shortly after I'd done this work and started the write-up, I found
[this
post](http://hypernephelist.com/2014/09/16/sending-data-to-azure-event-hubs-from-nodejs.html)
from Hypernephelist that covers much of the same ground.  If only I'd
found it a week sooner!  It doesn't cope with AMQP, and it doesn't
package things up into a `package.json`-includable form, so I thought my
post still had value.

