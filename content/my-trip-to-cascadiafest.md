Title: My Trip to CascadiaFest
Date: 2015-08-11 11:37
Author: noodlefrenzy
Category: Software
Tags: AMQP, Cascadia, Conferences, Javascript, Nitrogen, Node
Slug: my-trip-to-cascadiafest
Status: published

... or "who knew there was anything in Blaine, Washington?"

I got back recently from giving my first talk at [CascadiaFest
2015](http://2015.cascadiajs.com/), held in the beautiful Semiahmoo
Resort outside of Blaine, WA. As a long-term Seattle resident, my only
knowledge of Blaine was as "that place where we spend too much time
waiting to cross the border", but it turns out there's a beautiful golf
resort right nearby. Since I don't golf I still wasn't that excited, but
CascadiaFest had more than enough activity to keep me busy.

What is CascadiaFest?
---------------------

CascadiaFest is the renamed CascadiaJS, and is a regional web technology
conference. It's expanded beyond client-side Javascript to server-side,
and now to CSS (hence the rename), but really any talks related to
developing for the web are likely welcome, as well as those using JS in
more interesting ways. In fact, one of the talks this year was on
developing Minecraft mods using JS. Even though it's a regional
conference, several of the speakers and some of the attendees came from
elsewhere - I met a few from New York and one from Argentina, and saw
others from even farther afield.

### Logistics

The conference was held at the [Semiahmoo
Resort](http://www.semiahmoo.com/), which was actually quite
beautiful. [![Sunset at Semiahmoo
Resort](http://www.mikelanzetta.com/wp-content/uploads/2015/08/20150710_203724-300x169.jpg)](http://www.mikelanzetta.com/wp-content/uploads/2015/08/20150710_203724.jpg)

The grounds were large, it was surrounded by water, had a spa and a
pool - honestly I had no idea there was any place this nice between
Seattle and Canada. [![Semiahmoo Resort coastal pic during the
day](http://www.mikelanzetta.com/wp-content/uploads/2015/08/semiahmoo_coast-300x169.jpg)](http://www.mikelanzetta.com/wp-content/uploads/2015/08/semiahmoo_coast.jpg)The
lines to get in on the first day were long - it seemed like if they'd
let people check in the night before, they could have prevented some
initial headaches.
[![cascadia\_line](http://www.mikelanzetta.com/wp-content/uploads/2015/08/cascadia_line-300x156.jpg)](http://www.mikelanzetta.com/wp-content/uploads/2015/08/cascadia_line.jpg)But
once that initial hurdle was passed, the rest of the conference was
incredibly well run. The conference badges were far beyond any I've ever
received[![Cascadia Speaker
Badge](http://www.mikelanzetta.com/wp-content/uploads/2015/08/cascadia_badge-188x300.jpg)](http://www.mikelanzetta.com/wp-content/uploads/2015/08/cascadia_badge.jpg)

- solid laser-etched wood, definitely one to be kept. There was some
other swag, including a great CascadiaFest hoodie, but the badge was a
real standout. Plenty of sponsors were on-board providing lunch and
dinner, and the speakers-only dinner gave me a chance to get to know my
fellow speakers better. Overall the sense of camaraderie amongst
attendees was strong, making it by far the friendliest conference I've
attended.

The Talks
---------

The conference was broken thematically into three days, with a single
track of talks each day in a large room holding \~400 people. All talks
were uploaded to Youtube and auto-captioned.

https://www.youtube.com/embed?listType=playlist&width=474&height=266&list=PLLiioAbFTbKNpjG\_yNpNfhAmQ9KsxFzX7&plindex=0&layout=gallery

### Day One - CSS Day

The first day was CSS day, and the talks were mostly on CSS, but with a
few on more general topics. Take a look at the playlist above for the
full set, but I'll call out a few.

Alan Mooiman had a solid start to the conference with a talk on the
history and future of CSS, and why the cycle of birth and death in
preprocessors is a good thing.

https://www.youtube.com/watch?v=jWDZP8twWDg

Amy Lynn Taylor's talk started out slow, but had some great insights on
how to make a distributed team cohere and have a common culture. As
someone who works from home / remotely much of the time, it was relevant
to my interests.

https://www.youtube.com/watch?v=\_NPLqrVMHFw

### Day Two - Client-side Javascript Day

There was a great talk on JSON Web Tokens (vs. Cookies) by Martin
Gontovnikas with some easy examples to follow and motivating reasons to
use them.

https://www.youtube.com/watch?v=mvS4oxHFXxM

My colleague David Catuhe had a great talk on his Babylon.js library for
developing 3D games in Javascript. I can't wait to try it out, and with
easy importing from Unity it's much more likely I might actually do so.

https://www.youtube.com/watch?v=ZE-HRoaN4YE

Myles Borins had a great talk with a deceptive title - "On the
fallibility of large systems" made me think it was going to be about
distributed systems and fault-tolerance, but instead it was on how our
easy use of large dependency-chains can cause exciting failures you'd
never expect. A useful reminder for anyone using npm and Bower.

https://www.youtube.com/watch?v=47XMs6pcf7w

Andrei Kashcha's talk on visualization of huge graphs was fantastic. His
delivery was charming and his enthusiasm was infectious, and the
insights he was able to pull from these large graphs of package manager
dependencies like npm were illuminating.

https://www.youtube.com/watch?v=vZ6Yhlxv7Os

Ashley Williams had a talk on ES6 that was both great and somewhat
depressing. Depressing mostly because I'm not a huge fan of the JS
language, and her point that JS is a teaching language due to its
ubiquity and popularity rang true. I agree with her insight into the
oddness of adding classes to ES6 given JS's prototypal inheritance - I
hadn't considered it before, but it does seem out of place.

### Day Three - Server-side Javascript Day

Another of my colleagues - Parashuram - gave a talk on automating web
performance measurement that had some great details on how to integrate
that into your development process, and how to avoid pitfalls in the
process.

https://www.youtube.com/watch?v=86LwhTD\_rkM

And finally my talk on the [Nitrogen](http://nitrogen.io/) framework and
the development of my [AMQP messaging
client](https://github.com/noodlefrenzy/node-amqp10). I used
[Reveal.js](http://lab.hakim.se/reveal-js/#/) for my slides and
[open-sourced them on
GitHub](https://github.com/noodlefrenzy/Cascadia2015-NitrogenPres/tree/gh-pages),
using gh-pages for [hosting them](http://aka.ms/cascadia).

https://www.youtube.com/watch?v=99zXI6CZNGM

Final Thoughts
--------------

The whole CascadiaFest crowd were incredibly supportive - from the
attendees to the organizers. I would highly recommend this conference to
anyone in the Pacific Northwest who is interested in CSS or Javascript -
regardless of where it's held next year, you'll have a great time and
learn quite a bit.

I'd also like to give a shout-out to [Tougo
Coffee](http://www.tougocoffee.com/) for keeping me wired throughout the
entire three-day period, and whatever genius on the CascadiaFest team
who decided to bring them up to Semiahmoo.

 

