Title: I Miss Integers
Date: 2015-01-12 16:53
Author: noodlefrenzy
Category: Software
Tags: Javascript, Random musings, weirdness
Slug: i-miss-integers
Status: published

One of the worst things about working with Node.js is the .js part - as
much as I like Node, I still think JavaScript is a strange, broken
little language.  Not quite OO, not quite functional, it's a language
made to help browsers validate form fields and is now stuck trying to
cope with managing server-side processing at scale.  I may not like it,
but I have to give it props - I'm impressed.

However, it does have some eerie warts due to its bizarre type system,
and I'll be doing a few different posts calling those out.  Today's post
is on integers - you know, those shiny little numbers that can be
positive or negative and are infinite, but only countably-infinite.
 Most languages, in a nod to the practicality of finite computing, have
scoped the infinite down to 32-bit and 64-bit integers - Javascript has
neither.  It's chosen to embrace the "Number" - an IEEE754-encoded
floating-point meant to represent all numbers you might desire.

Most JavaScript programmers know this, and know that's why you can only
represent integers up to 2\^53, but there are some odd side-effects from
this choice, as I recently found out when trying to cope with 64-bit
integer values.  I knew I could only support up to 53 bits due to the
2\^53 constraint, so I was trying to do some bit-shifting and
bit-masking to separate things out into higher and lower order 32-bit
components.  In a language with unsigned longs, this might looks
something like  (Obviously, I'm ignoring details about sign, and using
simple operations - I don't want to stray too far from the point):

```csharp
ulong hi = (value & 0xFFFFFFFF00000000) >> 32;
ulong lo = (value & 0xFFFFFFFF);
```

What do you think this gives you in JavaScript?  I'll give you a hint -
it's not good.  Here's another fun example to call out the problem
specifically:

```js
alert(Math.pow(2,32) << 1 === Math.pow(2,32) >> 1)
```

Basically, operations on the upper 32 of a JavaScript Number mostly
result in zeros, leading to bizarre equality statements like the above.
 Unfortunately, since bit-shifting is a bitwise operation, those upper
32 are pretty much inaccessible without writing into a buffer of some
sort to get access to the bytes involved.

Bummer, but at least I know the rules of the game - 2\^32 == badness,
2\^31 or less == goodness.

So, imagine my surprise when I ran this code...

```js
alert((Math.pow(2,31) & Math.pow(2, 31)) === Math.pow(2, 31))
```

[![divide-by-zero-blog-safe[1]](http://www.mikelanzetta.com/wp-content/uploads/2015/01/divide-by-zero-blog-safe1-300x252.jpg)](http://www.mikelanzetta.com/wp-content/uploads/2015/01/divide-by-zero-blog-safe1.jpg)

