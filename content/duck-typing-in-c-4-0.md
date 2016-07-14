Title: Duck Typing in C# 4.0
Date: 2010-05-01 16:04
Author: noodlefrenzy
Category: Software
Tags: .NET, C#
Slug: duck-typing-in-c-4-0
Status: published

One of my favorite new features in C\# 4.0 is the <span
style="font-family: Consolas;"><span
style="font-size: small;">dynamic</span> </span>keyword.  Not only does
it allow you to do freaky things with interactions between C\# and
scripting languages like IronRuby, but it opens up one of my favorite
features from that language – *Duck Typing*.

*Duck typing* is like an interface without the rigor – a client just
assumes the class it’s calling has the method/property it expects, with
the semantics it hopes for.  For someone living in the world of
compile-time type safety, it can be a scary proposition, but it has its
benefits.

A trivial example, but one which suggests the power and uses of *duck
typing*, is below.  Three classes – all with different implementations
of IndexOf, adhering to no common interface – can be used without any
special casting, new delegate declarations, or other coercion.  This is
possible only through the ninja magic of <span
style="font-family: Consolas; font-size: small;">dynamic</span>.

First, we declare a class with a custom IndexOf method:

```csharp
public class BarContainer
{
  public int IndexOf(string str)
  {
    return "bar".Equals(str) ? 1 : -1;
  }
}
```

Next, in our main class we declare a method that uses our new class, as
well as a list and a string, and invokes the IndexOf method on each by
running them through <span
style="font-family: Consolas; font-size: small;">dynamic</span>:

```csharp
static void DuckTyping()
{
  string str = "foo, bar";
  BarContainer fake = new BarContainer();
  List<string> list = new List<string>(array);
  foreach (dynamic item in new object[] { str, fake, list})
  {
    Console.WriteLine("Item " + item.GetType() + " has 'bar' at position " + item.IndexOf("bar"));
  }
}
```

However, <span
style="font-family: cons; font-size: small;">dynamic</span> has some
limitations – sometimes surprising ones – that can limit its
usefulness.  The one that bites me the most is the lack of support for
extension methods.  Extension methods are a useful addition from C\# 3.0
that adds an almost *Mixin*-like functionality to the language, but due
to the way they are implemented (as static methods that work in
conjunction with a type, rather than as additions to the type itself),
they won’t work with<span
style="font-family: Consolas; font-size: small;">dynamic</span>.  Thus
the following code fails:

```csharp
public static class Extensions
{
  public static int IndexOf(this Array arr, string toFind)
  {
    for (int idx=0; idx < arr.Length; idx++) {
      if (toFind.Equals(arr.GetValue(idx)))
        return idx;
    }
    return -1;
  }
}

static void DuckTyping()
{
  string str = "foo, bar";
  string[] array = new string[] { "foo", "bar" };
  Console.WriteLine("See, extension method works here: {0}.", array.IndexOf("bar"));
  List<string> list = new List<string>(array);
  foreach (dynamic item in new object[] { str, array, list})
  {
    Console.WriteLine("Item " + item.GetType() + " has 'bar' at position " + item.IndexOf("bar"));
  }
}
```

This code is able to invoke IndexOf statically, but through the DLR it
fails with a <span
style="font-family: Consolas; font-size: small;">RuntimeBindingException</span>.

I think <span
style="font-family: Consolas; font-size: small;">dynamic</span> is a
fantastic and powerful addition to the language, but with great power…. 
As long as we’re careful with the types we use with it, and we
understand the limits imposed on us, I’m really looking forward to the
exciting future of static/dynamic hybrid code before us.

