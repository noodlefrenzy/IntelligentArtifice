Title: Java’s Checked vs. Unchecked Exceptions
Date: 2009-05-05 12:17
Author: noodlefrenzy
Category: Software
Tags: Java
Slug: javas-checked-vs-unchecked-exceptions
Status: published

I’m probably late to the party here (I’ve been in C\#-land lately), but
I think I’ve finally worked out what irks me about the Checked vs.
Unchecked Exception religious war in the Java world.  I’ve always been
on the Checked side of the fence, but lately there’s a whole host of
folks that I respect coming out in favor of Unchecked.  My problem is
this: declaring an exception “Checked” or “Unchecked” is actually
declaring it two different, largely orthogonal, things.  When you
declare that a method throws a Checked exception, you are making two
statements:

1. This exception is part of the signature of my method.
1. This exception must be dealt with by any method that calls me.

Let’s examine the second point in the context of a server application. 
If you have a server application, you expect it to continue running at
all times, unless something catastrophic happens.  For most of the
servers I’ve worked on, even things like failed SQL connections, full
disks, and classloader errors (in the face of misconfigured DI) didn’t
count as catastrophic – the server should continue, hopefully setting
off some alarms and perhaps doing what it can to clean itself up.  This
means that for just about any exception, it must be dealt with.

Let’s assume for a minute that we make the decision that MySQLException
is “catastrophic” and make it unchecked.  Our methods don’t declare it,
clients of ours don’t declare it, and all of a sudden our server
application crashes when it can’t get a connection – or worse yet it
catches it, but doesn’t know which of the ten DBs it uses is having the
problem and should be retried.

The obvious objection is that someone should be handling this exception
– but who?  The method that gets the connection probably shouldn’t be
the one trying to reconnect on failure, which means that some method
above that needs to manage the retry-or-fail logic.  This means, though,
that it needs to know when a failure has happened – and this is where I
start to hate unchecked exceptions.  In order for the method above it to
know when a retry-able vs. fatal error has happened, it needs to either
assume that RuntimeException means it can try again, or dig into the
code and figure out that MySQLException is throws for these cases.

Many folks will say that a good dev will put that sort of info into the
comments of the method (e.g. in a @throws clause), but there’s certainly
nothing requiring them to do so, and I’ve known plenty of devs that
wouldn’t (because it’s catastrophic, and what are clients going to do
about it?).  It seems odd to me that many of the same people arguing for
greater robustness and visibility in method/interface definition –
pre/post-condition definitions as part of the language, etc. – still
argue for unchecked exceptions.  I’m not saying they’re wrong, I’m just
outlining why I don’t like it.

So what do I like?  Wrapping.  Let’s take my example above again:  the
low-level method fails to get a connection, and throws a (checked)
MySQLException.  The calling method knows to catch it, and then
retries.  Say it keeps failing – then this higher-level method wraps the
MySQLException in a (checked) ResourceUnavailableException.  The
top-level method knows there’s an issue with the resource, and can
either die, fail the operation, or wait and try again later.

Wrapping doesn’t solve everything – there are some exceptions that
really should be unchecked (e.g. out-of-memory), and RMI changes
everything (don’t pass your inner MySQLException to someone who won’t
have that class loaded).  What it does is allow you to make your
interface explicit – even your error conditions – without forcing you to
throw exceptions at a low level your clients don’t want.  Exceptions are
a part of your interface, and should get the same care and attention as
the rest of it.

