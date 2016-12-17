Title: Caching Responses in Expressjs
Date: 2014-10-04 15:32
Author: noodlefrenzy
Category: Software
Tags: caching, Expressjs, memoization, Node
Slug: caching-responses-in-expressjs
Status: published

On a recent project, I found myself writing a web service in Node via
Azure Mobile Services, and realized that the client pattern was to call
a common set of requests on startup and in early interactions, and then
dig down into more detailed requests.  Furthermore, these common
requests were common across just about all clients.  Caching these
responses seemed like a natural thing to do, but the problem was that i
couldn't just cache the response object, I had to replay the previous
response so that the same status, headers, and body would be sent.  Also
I wanted the ability to control whether a request was cached based on
the content, and to avoid caching error responses.  I decided to write
it in such a way that others could potentially use it, and I've put it
[up on GitHub](https://github.com/noodlefrenzy/memoize-express).

For the backbone, I wrote a simple object - Replayer - that allows you
to wrap an object, trapping all function calls and recording all
parameters given, and then allowing you to replay those calls on another
object instance.  It does this by making a proxy function for all
functions on the object:

```js
function makeProxy(obj, replayer, fnName) {
    return function() {
        var args = Array.prototype.slice.call(arguments);
        replayer.record.push([ fnName, args ]);
        var result;
        if (args.length == 1) {
            result = obj[fnName].call(obj, args[0]);
        } else {
            result = obj[fnName].call(obj, args); 
        }
        return result === obj ? replayer : result;        
    };
}
```

Note that last line - this allows method-chaining APIs to work
correctly, so `res.status(200).body(data)` works as expected, with both
`status` and `body` being correctly recorded.

I use this "Replayer" ([packaged on
GitHub independently](https://github.com/noodlefrenzy/replayer), in case
it's useful on its own) within the Express Memoizer to record
all express request/response functions, leaving the actual memoizer
function pretty clean:

```js
Memoizer.prototype.memoize = function (fn) {
    var theCache = this.cache;
    var shouldCacheReq = this.shouldCacheRequest;
    var shouldCacheRes = this.shouldCacheResponse;
    return function(req, res) {
        if (shouldCacheReq(req)) {
            var key = requestKey(req);
            if (theCache.has(key)) {
                var prevRes = theCache.get(key);
                if (shouldCacheRes(prevRes.getWrapped())) {
                    prevRes.replay(res);
                    return;
                }
            }
            var fakeRes = replayer.watch(res);
            theCache.set(key, fakeRes);
            fn(req, fakeRes);
        } else {
            fn(req, res);
        }
    };
};
```

This checks the predicate for the incoming request to determine whether
it should be cached (if not, the call is just passed through), and then
checks the cache to see if the request is already cached.  If so, it
pulls the cached replayer instance, determines whether it should have
been cached, and if so then replays it on the current response object.

### Caveats

I was doing this to solve a particular problem, and also to learn how to
do some things in JS that I'm used to doing in other languages, so there
are plenty of caveats to this solution (and there might be other
solutions out there, although none of the existing memoization node
packages seemed to do what I needed).  I've documented them all in the
readme.md in each project, but I'll outline a few here as well.  First
off, the Replayer has three main caveats that would prevent wide
adoption, but didn't impact my use:

1.  It only wraps objects, so not on built-ins like String/Number.
2.  It stores the arguments literally, not in some serialized and then
    re-hydrated form, meaning that mutable objects could potentially
    change between the recording and the playback.
3.  It doesn't support async methods, so no invocation of callbacks,
    etc.

Additionally, it basically "duck-types" on playback, attempting replay
on whatever you've passed in, so if you've wrapped an object that has an
`indexOf` method, and eventually play it back on a string, it should
"work", but might not be the behavior you need (it will, however, be
[the behavior you
deserve]({filename}/images/hero-we-deserve.jpg)).
 The Memoizer inherits these caveats, and additionally has whatever
caveats are inherited by the cache implementation you use.  In addition,
the response predicate is only checked on retrieval from the cache, so
that there's no ordering dependence on how the caller chooses to invoke
response methods, and the memoizer doesn't need to keep track of
when/whether the response has completed.

