Title: SQL vs. NoSQL
Date: 2014-08-01 17:11
Author: noodlefrenzy
Category: Software
Tags: Distributed Systems, NoSQL
Slug: sql-vs-nosql
Status: published

I was recently asked by a colleague of mine why anyone is even using
NoSQL solutions at all, and not just sticking with SQL.  After telling
them that people use them because they're
[web-scale](https://www.youtube.com/watch?v=b2F-DItXtZs), I did some
thinking about when you should use NoSQL vs. just sticking with good old
SQL DBs.  If you look at the [original Dynamo
paper](http://s3.amazonaws.com/AllThingsDistributed/sosp/amazon-dynamo-sosp2007.pdf), it's quite clear that their goal was high scalability for workloads
while maintaining "high nines" availability.  Having worked at Amazon
(and been kept up all night with the sounds of pagers in my ears due to
Oracle alarms), I can understand their concerns.  For a case like their
shopping carts - hundreds of millions of highly-churned objects, no
connections between them, easily GET/PUT compatible - this makes perfect
sense, and it worked fantastically well.  Thus, the NoSQL revolution was
born, and everyone decided they needed to jump on the NoSQL train.

![I should use NoSQL](http://noodlefrenzy-wp.azurewebsites.net/wp-content/uploads/2014/08/nosql_cat.png)

The biggest problem with moving to NoSQL is the amount of functionality
you lose over regular RDBMSs - little things like "transactions",
"joins", "queries", "aggregation", "ACID guarantees" and "secondary
indexes" just to name a few.  These are big, important features, as is
obvious by how much
[Google](http://static.googleusercontent.com/media/research.google.com/en/us/archive/spanner-osdi2012.pdf)and
[others](http://www.mpi-sws.org/~druschel/courses/ds/papers/cooper-pnuts.pdf)spend
trying to [add](http://docs.mongodb.org/manual/indexes/)them back to
their existing NoSQL solutions.  If you need the scale and reliability
and can do without these features, then a NoSQL Key/Value store might be
the right answer for you.  NoSQL Document Stores (think MongoDB) give
you some of these features back (secondary indexing, queryability,
aggregates), but you're still transaction- and join-less.  Other more
arcane "NoSQL-ish" stores like Graph DBs can give you incredible
processing powers for particular types of data, and might suit your
needs (have you ever tried to write a graph query in SQL?).

However, the issue in adopting a NoSQL store goes deeper than deciding
what features you can live without - you need to know what happens to
your data.  When you commit a transaction in SQL, that data is committed
to disk, durable against reboots, and likely quickly spooled to a
secondary server - the fault patterns are well-known, and the behavior
of the various RDBMSs well and accurately documented.  With NoSQL,
you'll need to know about the [CAP
Theorem](http://en.wikipedia.org/wiki/CAP_theorem), where your chosen
store says it lies in the CAP triangle, and whether they're telling the
truth.

Kyle Kingsbury has a fantastic [series of blog
posts](http://aphyr.com/tags/jepsen) evaluating various stores on their
claims, and mostly finding them wanting - recommended reading if you're
thinking of adopting one for your own project. I'm not telling you to
avoid NoSQL stores - I've used my share, and written one (internal to
MS), and know how useful they can be.  Anyone considering NoSQL, though,
should go into it with eyes open, and consider whether SQL might work
better for their case.  With Azure, it's easy to spool up a SQL Server
instance *and* an instance of MongoDB, try both, and see which one you
like.

