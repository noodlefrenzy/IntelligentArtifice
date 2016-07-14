Title: Talking to EventHub with AMQP 1.0
Date: 2014-11-06 14:50
Author: noodlefrenzy
Category: Software
Tags: AMQP, Azure, EventHub
Slug: talking-to-eventhub-with-amqp-1-0
Status: published

Lately, I've been working on a Node.js-based library for speaking AMQP
1.0, since all of the existing ones are still on 0.9.1 and don't seem
intent on updating, or are based on Qpid Proton and thus burdened with
more native code than I'd like.  It's still very much a work in
progress, but if you'd like to follow it (or contribute) the whole thing
is [on GitHub](https://github.com/noodlefrenzy/node-amqp10).

One of the primary reasons for doing this work is to talk to the new
Azure EventHub - this platform for event processing is built for speed,
with great fan-in/fan-out characteristics that make it a natural for
working in the IoT space.  I love the way they've architected it (for
more details, check their [great overview
documentation](http://msdn.microsoft.com/en-us/library/azure/dn836025.aspx)),
but the lack of a consumption REST API makes it hard to work with from
Node.js - at least until my AMQP 1.0 library is complete.

One of the problems with AMQP 1.0, however, is it leaves so much of the
details of actually routing the send/receive of messages as an exercise
to the server implementor, so while the documentation says that with
EventHub "you can use any AMQP 1.0 client" - that doesn't really mean
anything unless you know how.  I went and sat down with the EventHub
team to get that information, and am posting it here so anyone else
using AMQP 1.0 clients can speak to EH easily, and I'll be working with
the team to ensure it makes it into the official documentation as soon
as possible.

I've phrased the sections below in a FAQ format - if you have additional
questions for how to use AMQP 1.0 against EH, let me know in the
comments section and I'll do my best to answer.

What is AMQP 1.0?
-----------------

Ok, if you don't know this then this post is probably not that
interesting to you, but AMQP 1.0 is the approved specification for AMQP
(Advanced Message Queuing Protocol) and is [published by
OASIS](http://docs.oasis-open.org/amqp/core/v1.0/os/amqp-core-complete-v1.0-os.pdf).
 It's basically a scorched-earth rewrite from AMQP 0.9, which is why so
few clients yet support it.  I'm not qualified to speak on the merits of
AMQP vs. other message queuing protocols out there, but they're all
better than vendor lock-in to MQSeries (or for that matter even MSMQ).
 In the below answers, where appropriate, I will refer to sections of
the specification linked above as AMQP\$section.

How Do I Authenticate?
----------------------

AMQP 1.0 supports [`SASL-PLAIN`](http://tools.ietf.org/html/rfc4616) for
sending credentials (AMQP\$5.3), and EventHub uses this for
authentication.  For EventHub, you open a connection to the ServiceBus
endpoint on the standard AMQP secure port, negotiate TLS, and then send
a SASL-PLAIN frame with either your ACS credentials, or you SAS key and
token as username and password.

How Do I Send Messages?
-----------------------

Sending messages is done by `ATTACH`ing to a terminus and sending
`TRANSFER` frames with message contents.  Within the `ATTACH` frame (see
AMQP\$2.7.3), there are `source` and `target` references - for sending
messages, you need to specify the name of your event hub (hereafter,
*\<my-event-hub\>*) as the `target`'s `address` field.  This will direct
messages to partitions as the EventHub chooses, allowing better fan-in
scaling.

When sending a message, in the message annotations (AMQP\$3.2.3) you
should specify the `x-opt-partition-key` setting to have whichever
string-based partition key you choose (e.g. the device ID) - this will
let EventHub hash that appropriately to its underlying partition scheme.
 If you decide you want to control your own fan-in and want fine-grained
partition management (generally, a bad idea unless you know what you're
doing), you *can* connect to a specific partition by
using *\<my-event-hub\>*/Partitions/*\<partition-name\>* as
your `target address`.

How Do I Consume Messages?
--------------------------

Well, that's the interesting part with EventHub - messages persist until
they time out and are destroyed, allowing multiple consumer groups to
consume the same message (or even the same consumer to consume it
multiple times) - this means messages aren't *"consumed"* in the
traditional queue-based sense.

Ok Then, How Do I Receive Them?
-------------------------------

Similarly to sending, you `ATTACH` to the EventHub terminus and receive
`TRANSFER` frames with the contents - but with some differences.
 When `ATTACH`ing to the EventHub, you should
specify *\<my-event-hub\>*/ConsumerGroups/*\<consumer-group-name\>*/Partitions/*\<partition-name\>*
as your `source address`.  The `$default` consumer group is guaranteed
to exist, so most people just use that one.  This means that you'll need
one Link (see AMQP\$2.6) for each Partition you wish to receive from.

Also, since EventHub doesn't keep track of which messages have been
consumed, it's up to clients to track that information and let the
EventHub know how to pick up from where they left off.  To make this
possible, each incoming message from an EventHub contains a message
annotation named `x-opt-offset`, which is an opaque string that allows
clients to keep track of (checkpoint) their place in the partition's
queue.  When they reconnect to a given partition, they can specify that
they want to pick up after their last checkpoint by using
the `filter` map on the `source`.

The AMQP spec is silent on what these filters are supposed to look like,
so EventHub has tried to use an existing quasi-standard in the space,
picking up [JMS' selector
filters](http://docs.oracle.com/cd/E19798-01/821-1841/bncer/index.html)
and their SQL92-ish syntax.  For this use, the `filter` key should be
Symbol`(apache.org:selector-filter:string),` and the value is
a "described type" (AMQP\$1.1.2) with the format Descriptor =
Symbol(`apache.org:selector-filter:string`), Value =
String(`amqp.annotation.x-opt-offset >` '*\<last-offset\>*')  (You think
that's ugly, you should see it in binary).

Wait, Then How Do I Know What Partitions Are Out There?
-------------------------------------------------------

Since you need to know the partition name to connect for consumption,
there are a few different mechanisms for getting the number, and
names, of the partitions - you don't need magic knowledge from the Azure
portal (although if you have it, feel free to use that instead).  First
off, there's a REST API to get those details,
e.g.: `GET /<my-event-hub>/ConsumerGroups/$default/Partitions` - this
will return an ATOM feed with the contents you need (keep in mind you'll
need the appropriate SAS headers - see my previous post on [talking to
EH from
Node](http://www.mikelanzetta.com/2014/09/talking-to-eventhub-from-node/)
for information about how to generate them).

If you want to keep it in the family, there's a way to get partition
information using AMQP itself, through the AMQP management API.
 ServiceBus supports a management endpoint that allows you to query
information directly from within AMQP by creating a Link to the
`source/target address` *\$management*.  You create a sender Link, send
a message asking for the information by specifying the following
properties (see AMQP\$3.2.4) and application properties (see
AMQP\$3.2.5):

```js
message.properties['message-id'] = '12345'
message.application-properties['operation'] = 'READ'
message.application-properties['name'] = '<my-event-hub>'
message.application-properties['type'] = 'com.microsoft:eventhub'
```

This will return a message on the receiver link with a body containing
an AMQP map with (at least) two elements: `partition_count` containing
the total number of partitions, and `partition_ids` containing the
partition names (an AMQP string array).

Conclusion
----------

Hopefully, this will help others when connecting to EventHub using AMQP.
 I'll keep updating this as I get more information, and please ask in
the comments if you have any additional questions.  Obviously, if you
have the option of using the existing .NET client - I'd highly recommend
that!  It's much easier than coordinating AMQP sessions yourself,
and you have someone besides yourself testing it.  Also, if all you're
doing is sending the occasional message to an EventHub from Node.js and
are not consuming them, please consider [my previous
work](https://github.com/noodlefrenzy/event-hub-client) (documented in
[my previous
post](http://www.mikelanzetta.com/2014/09/talking-to-eventhub-from-node/)) -
it uses the REST API and is generally easier to get up and running.
 However, if neither of those options work, hopefully this will give you
enough information to get up and running.  If you're looking for a
Node.js solution to working with AMQP1.0, I'm working on one, but it's
not there yet - if you feel like being a contributor, [come on
down](https://github.com/noodlefrenzy/node-amqp10) and help!

 

