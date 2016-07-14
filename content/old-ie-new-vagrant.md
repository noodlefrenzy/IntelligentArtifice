Title: Old IE, New Vagrant
Date: 2014-09-03 08:05
Author: noodlefrenzy
Category: DevOps
Tags: Web Development
Slug: old-ie-new-vagrant
Status: published

I've been messing around with
[Vagrant](http://www.vagrantup.com/ "Vagrant")for a few weeks now, on
and off, to manage my Linux VMs on my Win8.1 box with Hyper-V.  So far,
it's been working well, barring a few caveats due primarily to MSIT's
restrictive proxy settings (although I could find out it's really just a
[PEBKAC](http://en.wikipedia.org/wiki/User_error#Acronyms_and_other_names)issue).
 I love the idea behind the tool, as managing your dev box is a pain and
keeping VMs up to date is not much better.

Well, the folks at Modern.ie and my MSOpenTech colleague have now
converted a bunch of their VMs over to Vagrant!  If you're not familiar
with [Modern.ie](http://modern.ie) - it's a site the IE team set up to
ensure that folks didn't need to have a host of ancient Windows XP
machines with crufty IE6 installs in order to do cross-browser testing.
 They already had a host of VMs up there that'll run on everything from
Parallels to Virtual Box - this just extends those to allow you to
"vagrant up" whichever ones you need.  They're looking for people to
help them evaluate, to gauge interest and uncover issues - if you have
the need and the time, I would encourage you to go take a look, and read
the **[official blog
post](http://blog.syntaxc4.net/post/2014/09/03/windows-boxes-for-vagrant-courtesy-of-modern-ie.aspx "Modern.ie on Vagrant")**.

