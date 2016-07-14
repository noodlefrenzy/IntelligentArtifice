Title: “You can’t use that, it’s not performant”
Date: 2009-04-08 12:54
Author: noodlefrenzy
Category: Software
Tags: performance
Slug: you-cant-use-that-its-not-performant
Status: published

I can’t tell you how many times I’ve heard this - from PMs, dev leads,
and colleagues.  Other than the use of the “word” performant, what bugs
me about this is that usually they don’t have any data (or current data)
to back it up.  Coming from the Java world, I’ve probably heard it more
than most of my .NET colleagues, since Java is still accused of being
slower than X-Windows over a 300baud modem.

However, in the .NET world, this is increasingly used as an excuse to
hamstring new development and prevent the use of new features.  Luckily,
Vance Morrison has provided folks in the .NET world a way to verify
these claims, with his great MeasureIt tool, described in (and available
from) [this blog post of
his.](http://blogs.msdn.com/vancem/archive/2009/02/06/measureit-update-tool-for-doing-microbenchmarks.aspx)

I recently ran into one of these situations when I was told that I
couldn’t use the standard .NET XML Serializer and had to use the
XmlReader/Writer classes, because the serializer wasn’t “performant”
enough.  This could be a valid concern, but I didn’t believe it – mostly
because I didn’t want to write and maintain all of that reader/writer
code.  So I grabbed MeasureIt and went to work – I coded up four
different tests reading different size XML files with the schema I
needed: XmlReader, Xml Serializer, XPath, and LINQ to XML.  These tests
were not measuring how well these technologies worked in the general
case, but in my specific case, on my specific problem, and with my
specific coding irregularities.  I had the tests reviewed by some folks
on my team who knew a bit more about .NET + XML than I did, and then
went to town.

The graph below measures the time (in normalized time units, on the
left) to read different size XML files (on the bottom – the number of
high-level objects in the files).

[![image](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/Youcantusethatitsnotperformant_DB47/image_thumb.png "image")](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/Youcantusethatitsnotperformant_DB47/image_2.png)

Looking at the results, the XmlReader and Serializer implementation look
like they perform and scale pretty close to identically.  That’s pretty
impressive, and makes me wonder if the Serializer implementation uses
XmlReader/Writer under the hood.  I asked around, and it looks like
currently that is the way things are done (I’m not on the .NET library
team, so I could be wrong), and using sgen.exe with /k I took a look at
the generated serialization code and it looks terse.  These results
allowed me to justify my use of the serializer – making my code much
shorter and easier to test and maintain, at the cost of a very small
performance hit.

Performance is important, but it should be viewed as an overall part of
the design and development process.  Worrying about performance without
having concrete performance goals is a recipe for pain – MeasureIt is a
tool to allow you to start these sorts of performance conversations,
turning vague performance worries into concrete results that can be
discussed practically.  Once you start having these sorts of
conversations, you can advance to the point where you have concrete,
user-focused and testable performance goals – much easier to satisfy
than a vague sense of dread.

