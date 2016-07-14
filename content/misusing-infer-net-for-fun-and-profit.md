Title: Misusing Infer.NET For Fun and Profit
Date: 2009-12-04 22:21
Author: noodlefrenzy
Category: Software
Tags: .NET, ML
Slug: misusing-infer-net-for-fun-and-profit
Status: published

I’ve recently started looking
into [Infer.NET](http://research.microsoft.com/en-us/um/cambridge/projects/infernet/) –
I’m trying to learn some Bayesian inference, and it seems like a good
tool for the job (I’m a bear of little brain, and need all the help I
can get).  However, it’s an exciting library, so I’ve been playing with
it in other contexts – the subject of this post.

One thing I find myself doing on occasion is using random variables to
drive some heuristic, whether it’s messing about with genetic
programming or just driving some randomization in tests.  Currently, the
main way to do this is to instantiate a random number generator and use
it to generate either ints or doubles, using those values to drive
decisions:

```csharp
Random dist = new Random();
if (dist.NextDouble() <= 0.5)
{
// Do something...
}
```

With Infer.NET, you have a host of distributions to choose from, so you
can be a bit more selective.  For instance, if you were to implement the
above code using Infer.NET, you could use:

```csharp
Beta dist = new Beta(1,1);
if (dist.Sample() <= 0.5)
{
// Do something...
}
```

Using a [uniform Beta
distribution](http://www.wolframalpha.com/input/?i=beta+distribution+%281%2C1%29) to
provide a pseudo-random that matches the behavior above.  However, you
could go one step further:

```csharp
Bernoulli dist = new Bernoulli(0.5);
if (dist.Sample())
{
// Do something...
}
```

With a [Bernoulli
distribution](http://www.wolframalpha.com/input/?i=bernoulli+distribution),
you make your intent plain – a software coin-flip with the behavior as
expected.  I’m a big fan of making my intent plain when coding – it fits
my laziness theory, I’ll have less to remember the next time I look at
the code.

There are some [other
distributions](http://research.microsoft.com/en-us/um/cambridge/projects/infernet/codedoc/html/N_MicrosoftResearch_Infer_Distributions.htm) available
to you with Infer.NET, which you might find handy.  For instance,
sometimes I need to implement exponential backoff scenarios with
jitter.  Normally, I’d just use a simple random and fuzz uniformly
around the delay, but in many cases I’d prefer to have a tighter
grouping around the delay – one which a uniform distribution can’t
provide.  Now with Infer.NET, I can use
a [Gaussian](http://www.wolframalpha.com/input/?i=gaussian+distribution+%281%2C2%29):

```csharp
Gaussian dist = new Gaussian(1, 2);
// ...
delay += dist.Sample();
```

I realize these examples are somewhat contrived, but I’m excited by the
possibilities behind Infer.NET – both great and small – and examples
like these help me work through them.  I’m hoping that this post will
help bring Infer.NET to a wider audience - well, all two people who read
my blog :)

