Title: Node.js and .NET Talking EventHub, Together
Date: 2015-01-28 13:48
Author: noodlefrenzy
Category: Software
Tags: .NET, AMQP, Azure, C#, EventHub, Node
Slug: node-js-and-net-talking-eventhub-together
Status: published

Over the past few months, I've been working on [a Node.js client for
AMQP 1.0](https://github.com/noodlefrenzy/node-amqp10) - the *lingua
franca* of Azure's EventHub and ServiceBus.  Well, the EventHub support
is just about complete, and ServiceBus Topics and Queues should follow
shortly thereafter (it's just me working on it, so it's slow
going - \*hint\* PR's are welcome \*hint\*), so it seemed like a good
time to try to determine what it would take to interoperate between
Node.js and .NET using EventHub.  Turns out it's actually pretty simple.

AMQP Messaging Basics
---------------------

In order to understand the details, it's helpful if you understand how a
message is transmitted using AMQP first.  The message is sent using
a `Transfer` frame, with the body containing both the message payload as
well as any annotations.  In AMQP-speak, the body can be one of three
types:

-   `amqp-sequence `- a list of AMQP-encoded values
-   `amqp-value` - a single AMQP-encoded value
-   `data` - a blob of binary data in whatever format your little heart
    desires

Message annotations, if any, prefix the payload and are an AMQP map with
Symbol (`0xA3/0xB3` if you're speaking hex) or ulong keys and arbitrary
AMQP-encoded values.

Messages in EventHub
--------------------

When using EventHub in .NET with the `EventHubClient`, you encode data
by passing in an instance of an `XmlObjectSerializer` into `EventData`.
 It uses this to convert your payload object into a binary blob and pass
it using the `data` payload type I mentioned above.
 Now `XmlObjectSerializer` is a terribly named serializer interface, one
implementation of which is `DataContractJsonSerializer` (are you
beginning to see why the name is bad?).  This led me to believe that I
could use this on the .NET side to encode a `DataContract` object into
JSON and then decode it on the Node.js side easily - an assumption that
turns out to be true.  Symmetrically, I believed I could encode a JSON
string into a binary UTF8 buffer on the Node side and pass it to .NET
where it would then be easy to decode - that also turned out to be true.

EventHub also includes a few annotations with every message, letting
receivers know what the message's offset is, its timestamp and a few
other details, as well as accepting a partition-key annotation for
incoming messages.  I've altered my API to ensure I can support those
easily, without sacrificing generality for broader AMQP server cases.

Sending a Message from .NET
---------------------------

You can send a message from .NET by using the `EventData` type and
passing it to an `EventHubClient` instance's `Send` method.  To send a
JSON-based payload as I described above, you first need to define
a `DataContract` object like my `BasicData` here:

```csharp
[DataContract]
public class BasicData
{
    [DataMember]
    public string DataString { get; set; }

    [DataMember]
    public int DataValue { get; set; }
}
```

Then send it through your `EventHubClient` using
a `DataContractJsonSerializer` as my `Sender` class below illustrates:

```csharp
public class Sender
{
    private EventHubClient eventHubClient;

    public Sender(string connectionString, string eventHubPath)
    {
        this.eventHubClient = EventHubClient.CreateFromConnectionString(connectionString, eventHubPath);
    }

    public void Send(BasicData payload, string partitionKey = null)
    {
        var serializer = new DataContractJsonSerializer(typeof(BasicData));
        var data = new EventData(payload, serializer);
        if (partitionKey != null)
        {
            data.PartitionKey = partitionKey;
        }

        this.eventHubClient.Send(data);
    }
}
```

The connection string you use above should be the SAS connection string
from your Event Hub - one with Send permission.

Receiving a Message from Node
-----------------------------

To receive the message you just sent, you'll need to do more than
just say "connect" - EventHub doles messages out to different partitions
to do load balancing, and you need to read from each one in order to
find the message you just sent.  The PartitionKey you set above is a
proxy key that gets hashed into an actual partition, allowing you to
control load-balancing and group deliveries without having to see how
the sausage is made.  On .NET, this process is taken care of for you
(see below), but in Node you'll need to know how many partitions up
front and connect to them all.  My colleague and I are trying to change
that with [our node-sbus module](https://github.com/jmspring/node-sbus),
but it's not quite there yet.

So, using my `amqp10` module, how would you connect to a 16-partition
EventHub to read the message you just sent?  Well, the following code
snippet (taken mostly from `simple_eventhub_test.js` in that module)
demonstrates:

```js
var AMQPClient  = require('amqp10');

var uri = 'amqps://' + encodeURIComponent(sasName) + ':' + encodeURIComponent(sasKey) + '@' + serviceBusHost;
var sendAddr = eventHubName;
var recvAddr = eventHubName + '/ConsumerGroups/$default/Partitions/';

var client = new AMQPClient(AMQPClient.policies.EventHubPolicy);
client.connect(uri, function() {
    for (var idx = 0; idx < numPartitions; ++idx) {
        var curIdx = idx;
        var curRcvAddr = recvAddr + curIdx;
        client.receive(curRcvAddr, function (err, payload, annotations) {
            if (err) {
                console.log('ERROR: ');
                console.log(err);
            } else {
                console.log('Recv(' + curIdx + '): ');
                console.log(payload);
                if (annotations) {
                    console.log('Annotations:');
                    console.log(annotations);
                }
                console.log('');
            }
        });
    }
});
```

So you'll see the resulting message:

```js
Recv(15):
{ DataString: 'From .NET', DataValue: 16 }
Annotations:
{ descriptor: [Int64 value:114 octets:00 00 00 00 00 00 00 72],
  value:
   { 'x-opt-sequence-number': 1,
     'x-opt-offset': '120',
     'x-opt-enqueued-time': [Int64 value:1421795188160 octets:00 00 01 4b 09 98 dd c0],
     'x-opt-partition-key': 'PK5' } }
```

(Note the annotations - I'm using the
[node-int64](https://github.com/broofa/node-int64) module to ensure the
full fidelity timestamp is preserved.)

In the code above, you'll notice that I've automatically parsed the
UTF8-encoded JSON payload in the binary stream, by using a smart decoder
in the `AMQPClient.policies.EventHubPolicy` that you provided when you
instantiated the AMQPClient.  I mention this because you could write
your own encoders and decoders to do whatever processing you need to do.

```js
receiverLinkPolicy: {
    // ...
    decoder: function(body) {
        var bodyStr = null;
        if (body instanceof Buffer) {
            bodyStr = body.toString();
        } else if (typeof body === 'string') {
            bodyStr = body;
        } else {
            return body; // No clue.
        }
        try {
            return JSON.parse(bodyStr);
        } catch (e) {
            return bodyStr;
        }
    }
}
```

 Sending from Node
------------------

Now to reverse the process!  Sending from Node is easier than sending
from .NET, primarily because of the work I've done on making sure that
the encode/decode logic is set up to make the process easy, as part of
the `AMQPClient.policies.EventHubPolicy`:

```js
senderLinkPolicy: {
    // ...
    encoder: function(body) {
        var bodyStr = body;
        if (typeof body !== 'string') {
            bodyStr = JSON.stringify(body);
        }
        return new Buffer(bodyStr, 'utf8');
    }
}
```

So in order to send, you just connect and then send a JSON object:

```js
var client = new AMQPClient(AMQPClient.policies.EventHubPolicy);
client.connect(uri, function() {
    client.send({ "DataString": "From Node", "DataValue": msgVal }, sendAddr, 
                { 'x-opt-partition-key' : 'pk1' }, function() { ...
```

Setting the partition key isn't quite as simple as in .NET, but it's
pretty easy - you just set the appropriate value in the annotations
map.  EventHub uses an AMQP message annotation with the symbol
key `x-opt-partition-key` to delineate the partition key - my API does
the hard work of turning your object into that AMQP gunk.

Receiving Messages from .NET
----------------------------

To receive these messages on the .NET side, we're using the
EventProcessorHost - the oddly named processor library that not only
reads from all EventHub partitions, but stores offset data into blob
storage so it can pick up where it left off (or collaborate across
hosts).  The logic here is more complex than in the sending case,
because we have to implement an instance of `IEventProcessor` to process
incoming messages.  I've done a rather simple implementation that just
logs to the console and occasionally writes a checkpoint snapshot of the
offsets to blob storage:

```csharp
public class SimpleEventProcessor : IEventProcessor
{
    private static readonly TimeSpan TimeBetweenSnapshots = TimeSpan.FromMinutes(5);

    private PartitionContext partitionContext;
    private Stopwatch checkpointStopwatch;
    private SemaphoreSlim checkpointLock = new SemaphoreSlim(1);

    public async Task CloseAsync(PartitionContext context, CloseReason reason)
    {
        Console.WriteLine("Processor closing.  Partition '{0}', {1}.", context.Lease.PartitionId, reason);
        if (reason == CloseReason.Shutdown)
        {
            await context.CheckpointAsync();
        }
    }

    public Task OpenAsync(PartitionContext context)
    {
        Console.WriteLine("Processor opening.  Partition '{0}', Offset '{1}'.", context.Lease.PartitionId, context.Lease.Offset);
        this.partitionContext = context;
        this.checkpointStopwatch = Stopwatch.StartNew();
        return Task.FromResult(true);
    }

    public async Task ProcessEventsAsync(PartitionContext context, IEnumerable<EventData> messages)
    {
        var serializer = new DataContractJsonSerializer(typeof(BasicData));
        foreach (var eventData in messages)
        {
            var key = eventData.PartitionKey;
            var payload = eventData.GetBody<BasicData>(serializer);

            Console.WriteLine("Partition '{0}': Received PK: {1}, DataString: '{2}', DataValue: {3}.",
                context.Lease.PartitionId, eventData.PartitionKey, payload.DataString, payload.DataValue);
        }

        await this.checkpointLock.WaitAsync();
        try
        {
            if (this.checkpointStopwatch.Elapsed > TimeBetweenSnapshots)
            {
                await context.CheckpointAsync();
                this.checkpointStopwatch.Reset();
            }
        }
        finally
        {
            this.checkpointLock.Release();
        }
    }
}
```

I use the `SemaphoreSlim` to allow me to gatekeep access to the
stopwatch without forcing a synchronous lock.  Using this processor, I
then just register it for a given hub and consumer group:

```csharp
public class Receiver : IDisposable
{
    private string blobConnectionString;
    private string serviceBusConnectionString;
    private EventHubClient eventHubClient;
    private EventProcessorHost eventProcessorHost;

    public Receiver(string blobConnectionString, string serviceBusConnectionString, string eventHubPath)
    {
        this.blobConnectionString = blobConnectionString;
        this.serviceBusConnectionString = serviceBusConnectionString;
        this.eventHubClient = EventHubClient.CreateFromConnectionString(serviceBusConnectionString, eventHubPath);
    }

    public async Task Receive(string receiverName, string consumerGroupName = null)
    {
        var consumerGroup = consumerGroupName == null ?
            this.eventHubClient.GetDefaultConsumerGroup() :
            this.eventHubClient.GetConsumerGroup(consumerGroupName);
        if (this.eventProcessorHost != null)
        {
            await this.eventProcessorHost.UnregisterEventProcessorAsync();
        }

        this.eventProcessorHost = new EventProcessorHost(receiverName, this.eventHubClient.Path, consumerGroup.GroupName, 
            this.serviceBusConnectionString, this.blobConnectionString);
        await this.eventProcessorHost.RegisterEventProcessorAsync<SimpleEventProcessor>();
    }

    #region IDisposable Support
    private bool disposedValue = false; // To detect redundant calls

    protected virtual void Dispose(bool disposing)
    {
        if (!disposedValue)
        {
            if (disposing)
            {
                if (this.eventProcessorHost != null)
                {
                    this.eventProcessorHost.UnregisterEventProcessorAsync().Wait();
                    this.eventProcessorHost = null;
                }
            }

            disposedValue = true;
        }
    }
    public void Dispose()
    {
        Dispose(true);
    }
    #endregion
}
```

This will receive all messages sent since the last time the code was
run, storing information about the offsets for the different partitions
in blob storage.

Conclusion
----------

I realize there is a lot of code in this post, but there's not a lot of
boilerplate, and it's pretty easy to follow.  Getting .NET and Node
to interoperate and exchange data via EventHub, at high scale, is pretty
easy and opens up some great possibilities in the area of IoT, with
small Node-capable devices or hubs writing to EventHub and C\# or
F\#-based workers processing EventHub data-streams computing aggregates,
doing predictive analytics, or driving future work.  I hope I've fired
up some of you to play around with EventHub - I'd love people to use my
module, and if you have any feedback please let me know, either through
comments here or through pull requests :)  Happy eventing!

 

