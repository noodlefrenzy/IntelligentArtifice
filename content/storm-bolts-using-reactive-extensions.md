Title: Storm Bolts Using Reactive Extensions
Date: 2015-04-07 11:03
Author: noodlefrenzy
Category: Software
Tags: .NET, Apache Storm, C#, Distributed Systems, Reactive
Slug: storm-bolts-using-reactive-extensions
Status: published

As you might have noticed in some of my other posts, I've spent my share
of time with Azure EventHubs.  It's a great ingestion pipeline able to
cope with some of the highest scale workloads you can throw at it, but
once the data is in there it's another matter to pull it out and do
something useful with it.  You need a system capable of processing
multiple input streams at extremely high scale and combining them in
various ways, building aggregates, and storing results.  Apache Storm is
one such system, as are Spark and Azure Data Factory which I will
discuss in future posts.  It's quite easy to get Storm up and running on
Azure and it's easy to code the requisite pieces in C\#, but the Storm
architecture has some idiosyncrasies which make it difficult to decouple
the business logic of processing your data from the Storm-specific code
for managing the appropriate pieces and ensuring reliability semantics.
This post, in particular, discusses turning the Storm workflow on its
head using the Reactive Extensions allowing me to decouple the
Storm-specific code from my business logic in an elegant fashion.  In
a future post I will discuss using this structure to process input
from EventHubs. Programming note: all of the code in this post is
[available on GitHub](https://github.com/noodlefrenzy/ReactiveStorm).

Into the Storm
--------------

![topology]({filename}/images/topology1.png)

Like any other data processing pipeline, Apache Storm consists of a way to
get data into the system followed by a series of processing
steps resulting in one or more data outputs.  In Storm, the
input consists of "Spouts" which produce data in the form of "Tuples".
 One or more Spouts can then drive processing elements called "Bolts"
which ingest that data and may emit additional Tuples of their own.
 Eventually these chains of Bolts might produce one or more outputs
which would get stored to whichever data stores you have configured.
 Storm has a robust and tune-able fault tolerance model, with Tuples
allowing themselves to be "anchored" to downstream Tuples, and only
"done" when the entire dependency chain is successfully "ack'd". For
more details I'd encourage you to [peruse their
documentation](http://storm.apache.org/documentation/Guaranteeing-message-processing.html) which,
on this subject, is actually solid and well-written.

Storm on HDInsight, on Visual Studio
------------------------------------

To get started with Storm on HDInsight make sure you've installed the
HDInsight Azure tools for your version of Visual Studio - there's a
[great post on the Azure
site](http://azure.microsoft.com/en-us/documentation/articles/hdinsight-hadoop-visual-studio-tools-get-started/)on
installing the tools, connecting to your subscription and getting
started.  You'll notice a host of new project types specifically for
working with HDInsight once you've installed it and restarted VS - we
want "Storm Application".

![HDInsight -> Storm Application]({filename}/images/create_storm_project.png)

When you create the project, you'll wind up with a C\# Class Library
project with a few files you can use as templates to build out your
storm Topology - we'll be replacing most of those, as outlined below.
 Notice that although Storm itself seems like a stream-processing
system, in reality what it's doing is producing Tuples from within
Spouts using `NextTuple()` and consuming those Tuples (and potentially
producing more) from within the Bolt's `Execute()` method.
 Architecturally for Storm this makes sense, but for the user it's a bit
of a disconnect from how they think about the problem.  I know for me I
think of it as processing a stream of input into one or more streams of
output, and so had mentally geared myself for `Enumerables`
and `yield return` blocks, but instead I've almost got the dual of
that - I'm seeing a single element at a time, and sending a single
element at a time back out.  I immediately thought of Reactive
Extensions and `IObservable -` [the dual
of `IEnumerable`!](http://csl.stanford.edu/~christos/pldi2010.fit/meijer.duality.pdf)

First we need to add Reactive to the mix - open the "Manage NuGet
Packages" dialogue, and search for Rx-Main.  Add that to the project,
and you will now have access to the whole Reactive toolkit - from
`Subjects` to `Reactive.Linq`.  I'd definitely recommend spending some
time learning the framework if you don't know it - it'll break your
brain, but it's kind of amazing when you start wielding its power.  I'd
suggest this [paper on design
guidelines](http://go.microsoft.com/fwlink/?LinkID=205219), and this
[series of Channel 9
videos](http://channel9.msdn.com/Search?term=reactive%20extensions%20api%20in%20depth#ch9Search).

Building a Reactive Bolt
------------------------

Now to the implementation!  So the first thing we want to do is turn
this Bolt inside-out - we'll have an `Observable` of the Bolt's inputs
mapping through some processing to an `Observable` of the Bolt's
outputs.  We can factor out the logic that turns these Tuples into input
types and turns the output types into Values, and then the processor can
just focus on the logic itself.  These inputs and outputs should keep
track of the Tuples they've used so we can, if needed, anchor the output
of the Bolt as appropriate.  To do so, we'll wrap these inputs and
outputs in a couple simple parameterized structs:

```csharp
/// <summary>
/// Wrap the (converted) input to keep track of the original tuple for anchoring.
/// </summary>
public struct BoltInput<TIn>
{
    public SCPTuple Original { get; set; }
    public TIn Converted { get; set; }
}

/// <summary>
/// Wrap the result to keep track of all tuples that should anchor to the output.
/// </summary>
public struct BoltOutput<TOut>
{
    public IEnumerable<SCPTuple> Anchors { get; set; }
    public TOut Result { get; set; }
}
```

Since we now have several responsibilities and since the topology
builder likes each Bolt to be a distinct class, we'll turn this Reactive
Bolt into a nice abstract base class taking on the grunt work of
Reactifying (*is that a word?*) the code and leaving the child class to
just do the basics.  The result looks like this:

```csharp
public abstract class ReactiveBoltBase<TIn, TOut> : ISCPBolt
{
    public ReactiveBoltBase(Context context)
    {
        this.Context = context;
        MapSchemas(this.Context);
        this.Input = new Subject<BoltInput<TIn>>();
        ProcessInput(this.Input).Subscribe(
            output =>
            {
                var converted = this.ConvertOutput(output.Result);
                if (output.Anchors != null && output.Anchors.Any())
                {
                    this.Context.Emit(Constants.DEFAULT_STREAM_ID, output.Anchors, converted);
                }
                else
                {
                    this.Context.Emit(Constants.DEFAULT_STREAM_ID, converted);
                }
            },
            err =>
            {
                Trace.TraceError(err.ToString());
            },
            () =>
            {
                Trace.TraceInformation("Bolt shutting down.");
            });
    }

    private Context Context { get; set; }

    /// <summary>
    /// IObservable for the input data - fed to the processor.
    /// </summary>
    private Subject<BoltInput<TIn>> Input { get; set; }

    /// <summary>
    /// Execute now just feeds the tuple to the observable (and, potentially, acks).
    /// </summary>
    public void Execute(SCPTuple tuple)
    {
        this.Input.OnNext(
            new BoltInput<TIn>()
            {
                Original = tuple,
                Converted = this.ConvertInput(tuple)
            });
    }

    /// <summary>
    /// Map schemas into the Context using DeclareComponentSchema.
    /// </summary>
    protected abstract void MapSchemas(Context context);

    /// <summary>
    /// Convert SCPTuple into the input type.
    /// </summary>
    protected abstract TIn ConvertInput(SCPTuple tuple);

    /// <summary>
    /// Convert output type into Values for Emitting.
    /// </summary>
    protected abstract Values ConvertOutput(TOut output);

    /// <summary>
    /// Process the input data from its observable into output data.
    /// </summary>
    protected abstract IObservable<BoltOutput<TOut>> ProcessInput(
        IObservable<BoltInput<TIn>> input);
}
```

So there are only four methods that child classes need to implement.
 This may seem like more than it needed to in the first place (because
it is), but each of those is focused on a very specific task.
 `MapSchemas` is used to tell the `Context` what the input and output
schemas look like.  `ConvertInput/ConvertOutput` just convert values
from/to the input/output formats expected by Storm, and `ProcessInput`
does the meat of the work - subscribing to the input observable and
letting us watch for output.  The Bolt itself just `Subscribes` to the
`IObservable` handed back from `ProcessInput`, and `Emits` results as it
sees them (anchored appropriately).  That leaves `Execute` to just
publish inputs to the `Subject`, driving the `ProcessInput` logic.

Making Your Spout Reactive
--------------------------

Spouts are a bit tougher to make Reactive, primarily because even though
it's just an Emitter it has no control over when it emits. Storm drives
it through calls to `NextTuple`, which for good or ill is how Storm does
flow-control. We should honor Storm's wishes and not just flood the
stream by emitting everything the first time `NextTuple` is called.
 There are a couple of options for this throttling: for instance, we
could internally queue up our outputs and then dequeue when asked in
`NextTuple`.  However, going this route we might as well skip Reactive
since it really provides no value - and that's a perfectly acceptable
solution! It just doesn't make for much of a blog post, so let's dig a
little.

The other option is to put in some sort of gate. Every time the
`Observable` wants to produce a value it hits the gate, and if it has
capacity it goes through; every time `NextTuple` is called it adds a
unit of capacity to the gate.  In C\#, the way we implement this sort of
logic is with a `SemaphoreSlim` - we `Wait()` on the capacity of the
gate, and we `Release()` more capacity when asked.  Also since we're
going Reactive anyway, let's turn the Ack/Fail calls into an
`Observable` people can subscribe to.  Putting this all together results
in the class below:

```csharp
public abstract class ReactiveSpoutBase<TOut> : ISCPSpout
{
    public ReactiveSpoutBase(Context context)
    {
        this.Context = context;
        this.MapSchema(this.Context);
        this.Credits = new SemaphoreSlim(0);
        Task.Run(() =>
        {
            this.GenerateOutput().Subscribe(
                output =>
                {
                    this.Credits.Wait();
                    this.Context.Emit(Constants.DEFAULT_STREAM_ID,
                        this.ConvertOutput(output));
                },
                err =>
                {
                    Trace.TraceError(err.ToString());
                },
                () =>
                {
                    this.AckFailMessages.OnCompleted();
                });
        });
    }

    protected Subject<Tuple<long, bool>> AckFailMessages = new Subject<Tuple<long, bool>>();

    private Context Context { get; set; }

    private SemaphoreSlim Credits { get; set; }

    protected abstract void MapSchema(Context context);

    protected abstract Values ConvertOutput(TOut output);

    protected abstract IObservable<TOut> GenerateOutput();

    public void NextTuple(Dictionary<string, object> parms)
    {
        this.Credits.Release();
    }

    public void Ack(long seqId, Dictionary<string, Object> parms)
    {
        this.AckFailMessages.OnNext(Tuple.Create(seqId, true));
    }

    public void Fail(long seqId, Dictionary<string, Object> parms)
    {
        this.AckFailMessages.OnNext(Tuple.Create(seqId, false));
    }
}
```

Notice in particular the call to `Task.Run` when starting up the
subscription to `GenerateOutput` - this is just hedging our bets, making
sure that `NextTuple` isn't trying to Release on the same thread that
the emitter is Waiting on and avoiding potential deadlock situations.
 Also notice that akin to the Bolt, we've left the children to implement
just a few tightly-focused methods: `MapSchema` for telling the Context
about the output schema, `ConvertOutput` for turning the friendly output
type into the expected `Values` type, and `GenerateOutput` which does
the real heavy lifting.

A Simple Moving Average Example
-------------------------------

I know this is a lot of code and you may not really understand how it
all fits together until you see it in action, so let's code up a simple
example that turns a stream of integers into a moving average of the
last two entries.  First let's code up the spout. I'll leave out the
MapSchema and ConvertOutput calls because those are trivial (and all of
the source is [on
GitHub](https://github.com/noodlefrenzy/ReactiveStorm)if you're
interested) and focus on the meat of emitting a sequence of integers:

```csharp
public class RxIntSpout : ReactiveSpoutBase<int>
{
    public RxIntSpout(Context context) : base(context)
    {
        this.MaxValue = 10;
    }

    private int MaxValue { get; set; }

    protected override IObservable<int> GenerateOutput()
    {
        return Enumerable.Range(0, this.MaxValue + 1).ToObservable();
    }
    
    // ... some other stuff, elided ...
}
```

Wow, that's pretty simple.  Okay, now that that bit's complete, what
does it look like from the Bolt side - taking those integers and
emitting doubles of the 2-period moving average?  Once again, I've
removed some of the extraneous code (MapSchemas, ConvertInput/Output)
and focused on the core:

```csharp
public class RxMovingAverageBolt : ReactiveBoltBase<int, double>
{
    public RxMovingAverageBolt(Context context) : base(context) {}

    protected override IObservable<BoltOutput<double>> ProcessInput(IObservable<BoltInput<int>> input)
    {
        return input.Zip(input.Skip(1),
            (v1, v2) =>
            {
                var result = (v1.Converted + v2.Converted) / 2.0;
                Trace.TraceInformation("{0} + {1} / 2 = {2}", v1.Converted, v2.Converted, result);
                return new BoltOutput<double>() { Result = result };
            });
    }
    
    // ... some other stuff, elided ...
}
```

Okay, that looks pretty simple as well.  The only tricky bit there is
the `Zip` call where we basically join the incoming input to itself,
skipping the first value and resulting in pairs of values to be
averaged.  Even that's pretty simple to understand though.  Looks like
the conversion to Reactive is making the actual logic in the spouts and
bolts easier to understand and more separable, which was my goal in the
first place.

Testing Locally
---------------

Rather than set up a full Storm cluster just to test this out, you can
drive the Spouts and Bolts from within your main method fairly easily.
 First, you need to switch your project from a Class Library to a
Console Application - that's a simple drop-down on
Project-\>Properties-\>Application-\>Output type.  Now you can actually
run your code, so create a Main to exercise your Spout and then your
Bolt - it's not quite end-to-end since in reality there will be
interplay between the two, but it's close enough for testing purposes.
 The code to do so is below, and basically just creates instances of
each with their own local context, runs them, and stores off the
results.  The Bolt reads from the results of the Spout via the file
system - not necessary, but allows troubleshooting if intermediate
stages fail.

```csharp
// Let's watch the trace messages.
Trace.Listeners.Add(new ConsoleTraceListener());
SCPRuntime.Initialize();

var spoutCtx = LocalContext.Get();
var seqSpout = new RxIntSpout(spoutCtx, null);
while (/* ??? seqSpout has more values ??? */)
{
    seqSpout.NextTuple(null);
}
spoutCtx.WriteMsgQueueToFile("seq.txt");

var rxCtx = LocalContext.Get();
var rxBolt = new RxMovingAverageBolt(rxCtx);
rxCtx.ReadFromFileToMsgQueue("seq.txt");
rxCtx.RecvFromMsgQueue().ToList()
    .ForEach(tuple => rxBolt.Execute(tuple));
rxCtx.WriteMsgQueueToFile("rx.txt");

Console.WriteLine("Finished");
Console.ReadKey();
```

Pretty straightforward, but note the confusion in the while loop?  Since
we're pumping the Spout ourselves and need to finish when it's done with
its data, we need some way of knowing when that is.  We can add a simple
flag value to the `ReactiveSpoutBase` to track that for us:

```csharp
public ReactiveSpoutBase(Context context)
{
    // ...
    Task.Run(() =>
    {
        this.GenerateOutput().Subscribe(
            output => { /* elided */ },
            err => { /* elided */ },
            () =>
            {
                Trace.TraceInformation("Spout shutting down.");
                this.FinishedTransmitting = true;
                this.AckFailMessages.OnCompleted();
            });
    });
}

public bool FinishedTransmitting { get; set; }

// ...
```

and alter the while loop appropriately:

```csharp
while (!seqSpout.FinishedTransmitting)
{
    seqSpout.NextTuple(null);
}
```

You now have something you can run locally, which should produce output
like:

```
ReactiveStorm.vshost.exe Information: 0 : 0 + 1 / 2 = 0.5
ReactiveStorm.vshost.exe Information: 0 : 1 + 2 / 2 = 1.5
ReactiveStorm.vshost.exe Information: 0 : 2 + 3 / 2 = 2.5
ReactiveStorm.vshost.exe Information: 0 : 3 + 4 / 2 = 3.5
ReactiveStorm.vshost.exe Information: 0 : 4 + 5 / 2 = 4.5
ReactiveStorm.vshost.exe Information: 0 : 5 + 6 / 2 = 5.5
ReactiveStorm.vshost.exe Information: 0 : 6 + 7 / 2 = 6.5
ReactiveStorm.vshost.exe Information: 0 : 7 + 8 / 2 = 7.5
ReactiveStorm.vshost.exe Information: 0 : 8 + 9 / 2 = 8.5
ReactiveStorm.vshost.exe Information: 0 : 9 + 10 / 2 = 9.5
```

Summary
-------

Apache Storm is a promising pipeline processing technology, and with
HDInsight bringing it onto the Azure platform, deploying it yourself is
trivial.  However, writing all of the Spouts and Bolts can mean rewiring
your intuition a bit and mixing your business logic with Storm
internals.  Hopefully, by using Reactive and the code above, you can
make that process easier and provide better isolation between the two,
in a mental model that maps a bit better to what you're trying to
accomplish.  All of the code above is [published on
GitHub](https://github.com/noodlefrenzy/ReactiveStorm)- feel free to
clone it, modify it to your heart's content, and if you find any issues
file them or submit a PR.  I hope I've helped, and comments, as always,
are welcome.

