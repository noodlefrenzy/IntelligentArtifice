Title: Using Java Concurrency Primitives: ReadWriteLock
Date: 2009-10-21 21:54
Author: noodlefrenzy
Category: Software
Tags: concurrency, Java
Slug: using-java-concurrency-primitives-readwritelock
Status: published

So it’s been some time since I updated this blog, and I thought I’d
explain why just on the off-chance folks are actually reading. My wife
and I just bought a new house (well, town-house, we are in Seattle), and
that took (and is still taking) a lot of my time. In addition, we’re in
the process of preparing for a new release at work, so I’ve been quite
busy with that. Finally, our office just moved from Seattle to Bellevue
(Microsoft is not just in Redmond), and that’s been distracting (my
commute has gone from 20 to 60 minutes each way).

As of JDK 5, Java has added a host of new concurrency primitives that
allow you to fine-tune your code for multi-core scenarios (.NET has
added/is adding many more as of 4.0, but we’ll save that for future
posts).  I thought I’d do a few blog posts outlining how these new
primitives have helped me improve my code.  I’m not saying this is the
ideal way to do things, but they’re methods that have helped me and I
thought I’d pass them along.

First up – the synchronized keyword vs. explicit locking. 
java.util.concurrent.locks contains a few new lock types, with the
ReadWriteLock being my favorite.  Yet I still see a lot of code that
looks like this:

```java
/* Called a bunch */
public synchronized Object getStuff()
{
  return this.stuff;
}

/* Called on occasion, by some sort of timer */
public synchronized void computeNewStuff()
{
  // do some expensive computation to build new stuff object
}
```

There are a few improvements we could make to this code, but here we’re
focusing on using the new lock construct. 
The [ReentrantReadWriteLock](http://java.sun.com/javase/6/docs/api/java/util/concurrent/locks/ReentrantReadWriteLock.html) is
ideal for these cases, where the “stuff” object is read more than it is
written.  The above code could be restructured as follows:

```java
public Object getBetterStuff()
{
  this.lock.readLock().lock();
  try {
    return this.betterStuff;
  } finally {
    this.lock.readLock().unlock();
  }
}

public void computeBetterStuff()
{
  Object newStuff = null;
  // do some expensive computation to build newStuff
  this.lock.writeLock().lock();
  try {
    this.betterStuff = newStuff;
  } finally {
    this.lock.writeLock().unlock();
  }
}

private ReadWriteLock lock = new ReentrantReadWriteLock();
```

This contains two enhancements – first, we limit the locking period on
recomputation to just the piece of code where we’re storing the
newly-computed value.  This is doable even with existing constructs by
using an internal Object instance as a synchronization point.  Second,
we use the read-write lock to allow multiple readers to access the value
without contending with each other.  Only when we’re in the process of
setting the newly-computed value will readers be locked out.

This example is largely illustrative, though..  In reality, since we’re
only resetting one value under computation, there’s no need for such a
heavyweight solution and I’d probably just go with an AtomicReference:

```java
public Object getBestStuff() {
  return this.bestStuff.get();
}

public void computeBestStuff() {
  Object newStuff = null;
  // do some expensive computation to build newStuff
  this.bestStuff.set(newStuff);
}

private AtomicReference<Object> bestStuff;
```

I hope this proves useful for some folks.  I’m planning on following
this up with more posts about both Java and .NET constructs for
concurrency, and as always I welcome comments and suggestions on future
directions.

