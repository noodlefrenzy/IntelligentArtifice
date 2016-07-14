Title: Azure Storage: Architecture  Troubleshooting
Date: 2014-09-16 10:12
Author: noodlefrenzy
Category: Software
Tags: Azure
Slug: azure-storage-architecture-troubleshooting
Status: published

I've been dealing with Azure Storage for years now, and while most of
the time it's rock solid, on occasion you can get hit with networking
issues or other "brownout" drops in availability that can make you
question your sanity.  I find it helpful to know what's going on behind
the scenes in situations like that - mostly because I'm curious,
especially about how very large scale NoSQL stores are built, but also
because it can help you make sense of what might be happening.  The
Azure folks have written a [great
paper](http://sigops.org/sosp/sosp11/current/2011-Cascais/printable/11-calder.pdf)
on how their system is built, and why it "violates the CAP theorem"
(spoiler alert: it doesn't).  There's also [a
video](https://www.youtube.com/watch?v=QnYdbQO0yj4) of their talk that's
worth watching if you're into that sort of thing.

You might ask why I'm publishing a post on a 3-year-old paper as if it's
news.  Well, it was preamble for an incredibly thorough new guide on
[monitoring and diagnosing Azure
Storage](http://azure.microsoft.com/en-us/documentation/articles/storage-monitoring-diagnosing-troubleshooting/)
that the team just published.  This guide is quite detailed, giving
guidance on how to correlate client and server data, how to ensure
storage monitoring is enabled at the right level of granularity,
what spikes in different metrics mean in isolation or combination, and
appendices on setting up your favorite network monitoring tool to watch
storage traffic - I didn't even realize I wasn't supposed to be using
Netmon anymore :-\\.

Both the paper and the guide are worth a look - the guide is worth
reading *now* if you do any storage-related work, if only to make sure
you're gathering the right metrics for when you need them, and the paper
can wait for when you have some free time and want something a bit more
detailed.  Enjoy!

