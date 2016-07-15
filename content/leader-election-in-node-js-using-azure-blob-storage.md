Title: Leader Election in Node.js Using Azure Blob Storage
Date: 2015-11-18 15:58
Author: noodlefrenzy
Category: Software
Tags: Azure, Azure Blob, Distributed Systems, Node
Slug: leader-election-in-node-js-using-azure-blob-storage
Status: published

[Leader Election](https://en.wikipedia.org/wiki/Leader_election) is a
mechanism for designating one instance of a group as the primary (or
leader) and the others as secondaries (or followers), and is typically
used for coordination amongst groups of machines in a distributed
system. I first learned of leader election back in the olden times of
managing DBs, with hard-coded primary/secondary failover. Later with
coursework and practice in distributed systems, I learned various
algorithms for leader election - from
[Paxos](https://en.wikipedia.org/wiki/Paxos_(computer_science))'
"¯\\\_(ツ)\_/¯" (whoever gets their proposal accepted is the leader for
that round) to
[Raft's](https://ramcloud.stanford.edu/wiki/download/attachments/11370504/raft.pdf)stronger
notions. They all have one thing in common - if you don't *have* to
implement them yourself, don't do it! Distributed algorithms are
error-prone and hard.

Implementing distributed algorithms can be made somewhat easier by using
immutable-rich functional languages like Clojure or F\#, or languages
built for systems programming like [Rust](https://www.rust-lang.org/),
but what if you're stuck in something like Node.js, with all of the
type-safety of JavaScript and all of the garbage collection of C? Sure
it'd be a fun exercise, but not when you're up against a deadline.

The Goal of Leader Election
---------------------------

The goal of having a leader election is to ensure that for any given
resource only one instance is allowed to "control" it. With Paxos for
instance, any given round's result is "controlled" by the leader.

![Paxos algorithm
flow]({filename}/images/paxos1_sm.png)

With database failover the leader controls all writes and forwards them to
all followers. In the event of a leader failure that control should
lapse to another instance after a certain amount of time has elapsed.
Effectively, a leader is "leasing" control for a certain timeout period
and as long as they renew that lease they can remain in control.

Azure Blob Concurrency Control
------------------------------

Naturally this led me to think of Azure Blob Storage. Blobs have two
modes of concurrency control for writes - optimistic concurrency via
[etags](https://en.wikipedia.org/wiki/HTTP_ETag)and
[lease-based](https://msdn.microsoft.com/en-us/library/azure/ee691972.aspx)
concurrency. The [Node SDK for Azure
Storage](https://github.com/Azure/azure-storage-node) exposes blob lease
primitives via a few simple API calls - [grabbing a
lease](https://github.com/Azure/azure-storage-node/blob/master/lib/services/blob/blobservice.js#L1066),
[renewing
it](https://github.com/Azure/azure-storage-node/blob/master/lib/services/blob/blobservice.js#L1107),
and [releasing
it](https://github.com/Azure/azure-storage-node/blob/master/lib/services/blob/blobservice.js#L1185)
(plus a few others less relevant to this discussion). Once you have a
lease you can then mutate the blob to your heart's content by including
the lease ID in the options - at least until that lease lapses. Leases
by default are infinite (which makes *no* sense), but you can specify a
`leaseDuration` option of between 15 to 60 seconds to scope the
lease-hold time.

One of the things I didn't like about the Azure Node.js SDK, however,
was how hard it was to use for actually managing leases. You had to trap
return codes and look for already-held errors vs. other errors, it was
all callback-based, and there was a separation between the blob service
and the lease you were holding (i.e. you had to track the service
object *as well as* the lease ID in order to do anything useful). For
re-upping the lease you needed to register timeouts or intervals to
renew, and if those lapsed without successful renewal you somehow needed
to know that your lease ID was no longer valid (or trap that error the
next time you used it). It seemed like a collection of operations that
could be pulled up into their own class.

Cerulean Is Born
----------------

I created [node-cerulean](https://github.com/noodlefrenzy/node-cerulean)
as a module (named because cerulean is quite close to azure) to factor
out helper methods, classes, and utilities that would make using Azure
easier from within Node.js. Making Blob Leases easier to use would be
the first goal of this new module but more are guaranteed to follow -
and if you have any ideas do not hesitate to open
[issues](https://github.com/noodlefrenzy/node-cerulean/issues)or PRs.

#### Easier Leases

First off I needed to create a new `Lease` class for managing blob
leases that would have the following functionality:

-   Acquire a lease and make it easy to know when that succeeds or fails
-   Easily renew the lease
-   Release the lease when desired
-   Get the contents of the blob involved
-   Store new contents using the lease ID to manage access

I chose to use [Bluebird](https://github.com/petkaantonov/bluebird)to
promisify all of the operations to make it quite easy to trap
success/failure conditions for each without resorting to callback soup.

Looking at `Lease.acquire` you can see how I've just wrapped the
existing API so that I trap return values, store off the lease ID, and
invoke resolve/reject appropriately on the returned promise:

```js
Lease.prototype.acquire = function(options) {
    var self = this;
    return self.ensureContainerExists().then(function() {
        return self.ensureBlobExists();
    }).then(function ()
    {
       return new Promise(function (resolve, reject) {
           self.blobService.acquireLease(self.container, self.blob, options, function(error, result, response){
               if (error) {
                   reject(error);
               } else {
                   self.leaseId = result.id;
                   resolve(self);
               }
           });
       });
    });
};
```

Also note that before I attempt to acquire the lease I ensure that the
blob exists. Right now I do this each time, but I could easily tune this
to early-out that method if I've already checked or bypass it entirely
(e.g. based on a constructor flag that tells me it exists). It's also
possible to invert this and trap "does not exist" errors and only ensure
the blob exists if that happens.

The renew and release methods are implemented similarly, while the blob
get/update methods use the stored lease ID during access:

```js
Lease.prototype.updateContents = function(text, options) {
    var self = this;
    return new Promise(function (resolve, reject) {
       if (!self.leaseId) {
           reject(Lease.NotHeldError);
       } else {
           var opts = _.defaults({ leaseId: self.leaseId }, options || {});
           self.blobService.createBlockBlobFromText(self.container, self.blob, text, opts, function(error, result, response) {
              if (error) {
                  reject(error);
              } else {
                  resolve(self);
              }
           });
       }
    });
};
```

#### Managing Lease Acquisition and Loss

This makes leases much easier to manage, but it's still non-trivial to
implement leader election on this primitive and I wanted to make it as
easy as possible. To that end I've implemented a `LeaseManager` class
that given a lease will attempt to acquire it and renew it
automatically, and will warn you when it loses it.

This uses an eventing model rather than promises since it's a living
manager, where a lease can be acquired and lost multiple times and the
manager can manage multiple leases. It uses a stored interval per lease
to control whether it's in the "attempt to acquire" or the "attempt to
renew" phase, and it both aggressively renews and aggressively fails. It
renews every 15 seconds on a 60-second lease and reports lease loss when
the lease expiry period would fall outside the next renewal (rather than
waiting for a renewal to fail due to lease-loss error).

Let's take a look at the `manageLease` method which starts the process
and the `_acquire` method to which it delegates the majority of its
work:

```js
LeaseManager.prototype.manageLease = function(lease) {
    this.leases[lease.fullUri] = { lease: lease };
    this._acquire(lease);
};

LeaseManager.prototype._acquire = function(lease) {
    var self = this;
    var acquireLease = function() {
        lease.acquire({leaseDuration: LeaseManager.DefaultLeaseDuration}).then(function () {
            self._unmanage(lease);
            self.leases[lease.fullUri].expires = Date.now() + (LeaseManager.DefaultLeaseDuration * 1000);
            self._maintain(lease);
            self.emit(LeaseManager.Acquired, lease);
        }).catch(function (error) {
            debug('Failed to acquire lease for "' + lease.fullUri + '": ' + error + '. Will retry.');
        });
    };
    self.leases[lease.fullUri].interval = setInterval(acquireLease, LeaseManager.DefaultLeaseDuration * 1000);
    acquireLease(); // Best-case scenario, it acquires immediately and clears the interval.
};
```

Notice how I trap the lease in the `acquireLease` closure and call
`acquireLease` at the end - this is just because `setInterval` doesn't
have any sort of "invoke immediately" flag (or initial/repeat interval
params). The idea is that we immediately try and acquire the lease - if
that succeeds we move on to maintenance but otherwise we keep trying to
acquire. When we `unmanageLease` we can just clear the interval and
release the lease if we have it held.

Once we acquire the lease we emit a `LeaseManager.Acquired` event with
the lease we've grabbed and we keep track of the expiry timestamp. Every
time we renew the lease we update this expiry timestamp. If we fail to
renew we don't worry about it until the next renewal request would fall
outside the expiry period - at that point we immediately emit a
`LeaseManager.Lost` event and go back into acquire mode.

By "losing" the lease early we make a conscious choice that a longer
leaderless period is a better option than a possible
multi-head/multi-leader situation. However we're relying on two
assumptions of the Node.js framework that could be violated and my code
doesn't yet trap/error on these, so *caveat emptor* for now:

1.  Intervals execute roughly when we expect them to (e.g. no delays
    longer than hundreds of milliseconds)
2.  Callbacks are invoked roughly when the call succeeds, and latency
    between grabbing the lease and reporting success is relatively small

If either of these assumptions is violated our expiry time could be off
or our renewal could be delayed. Given the long lease time (60 seconds,
15-second renewal) this should not be an issue in practice but it is
something to be aware of, especially in a quasi-single-threaded
environment like Node.js.

Using the Lease Manager for Leader Election
-------------------------------------------

Now that we have a `LeaseManager` we can use it to do leader election
automagically quite easily. All we need to do is have multiple clients
attempt to manage the same `Lease` - whoever acquires it is the leader
(and is notified via the `LeaseManager.Acquired` event), and remains the
leader until they either `unmanageLease` or they receive the
`LeaseManager.Lost` event. Once they lose the lease all clients will
still be attempting to acquire the lease still, so one of them should
take over as leader as soon as the lease lapses.

You can see this in action in a simple integration test in the
`node-cerulean` module:

```js
it('should allow lease takeover', function(done) {
    var blobName = uuid.v4();
    var lease = new Lease(config.accountName, config.accountKey, config.containerName, blobName);
    var m1 = new LeaseManager({ leaseDuration: 15 });
    var managedByM1 = false;
    m1.on(LeaseManager.Acquired, function() {
       managedByM1 = true;
       m1.unmanageLease(lease);
    });
    var m2 = new LeaseManager({ leaseDuration: 15 });
    m2.on(LeaseManager.Acquired, function() {
        m2.unmanageLease(lease);
    });
    m2.on(LeaseManager.Released, function() {
        expect(managedByM1).to.be.true;
        done();
    });
    setTimeout(function() {
        m2.manageLease(lease);
    }, 2000);
    m1.manageLease(lease);
});
```

This test creates two clients (`m1` and `m2`) and attempts to manage the
same lease with both (with a 2 second delay on `m2`'s attempt, so it
"loses the race"). Once `m1` acquires the lease it is now the leader
(and records that fact). It then un-manages it (releasing it and
stopping itself from trying to re-acquire). As soon as `m2` re-tries to
acquire it will succeed, and at that point it has become the leader and
the test can succeed.

A more concrete and specific [example for leader
election](https://github.com/noodlefrenzy/node-cerulean/blob/master/examples/leader_followers.js)
can be seen in the [examples
directory](https://github.com/noodlefrenzy/node-cerulean/tree/master/examples).
You can take this example and run with it, creating your own
leader-based concurrent algorithms with confidence. I'll be using it as
the basis for V2 of my `node-sbus-amqp10` module allowing me to write
code that can seamlessly interoperate with the
[`EventProcessorHost`](https://www.nuget.org/packages/Microsoft.Azure.ServiceBus.EventProcessorHost)used
to manage Event Hub subscriptions in .NET (which I'll document in a
future post).

Once again, all of the code above lives on GitHub in my [node-cerulean
module](https://github.com/noodlefrenzy/node-cerulean) with the
permissive MIT license, and is published as npm module `cerulean`.

