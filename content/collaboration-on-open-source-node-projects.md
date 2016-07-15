Title: Collaboration on Open-Source Node Projects
Date: 2015-02-11 11:38
Author: noodlefrenzy
Category: Software
Tags: GitHub, Node, NPM
Slug: collaboration-on-open-source-node-projects
Status: published

I've been working on a [Node-based AMQP
1.0](https://github.com/noodlefrenzy/node-amqp-1-0) library and
[wrappers](https://github.com/noodlefrenzy/node-sbus-amqp10) that allow
it to talk ServiceBus and EventHub easily with a colleague of mine at
work, and it's taught me many things about doing Node.js
development, collaborating on GitHub, and publishing on npmjs.  The
documentation is mostly out there but it's a bit scattered, so I wanted
to gather it together into a common place to allow myself and others to
find it easily.

Starting a Project
------------------

There are a few different ways to start, but all involve getting GitHub,
Node, and npm installed on your machine.  For me, as a Windows user,
this means using [Chocolatey](https://chocolatey.org/ "Get Chocolatey"):

```batch
C:\> choco install git
C:\> choco install nodejs
C:\> choco install npm
```

However, if you're not a Windows user, install git [using the directions
on
git-scm](http://git-scm.com/book/en/v2/Getting-Started-Installing-Git),
and [node/npm
using apt-get](https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager)or
your package manager of choice.

Some people choose to create their projects by using `npm init`, but I
prefer to [create my new project on GitHub
first](https://help.github.com/articles/create-a-repo/ "Create a Repository"),
then go to where I want it on my local box and `git clone` it there.
 This makes it easy to automatically include an appropriate .gitignore,
README.md, and LICENSE file.  Now that you have your local copy, you
can `npm init` to get a `package.json` set up.

As a side note - you should consider adopting a coding standard for your
project.  It'll make it far easier for others to contribute in a common
style, and it'll keep your code looking clean and consistent.  One way
to codify this is to include an `.editorconfig` file - this
quasi-standard is a [simple configuration
format](http://editorconfig.org/) for codifying much of the standard
coding style choices you make, and with plugins for [Visual
Studio](https://github.com/editorconfig/editorconfig-visualstudio#readme)
and
[WebStorm/IntelliJ](https://github.com/JetBrains/intellij-community/tree/master/plugins/editorconfig),
makes keeping code consistent fairly simple.

Developing Your Node Module
---------------------------

*This is left as an exercise to the reader.*

Setting Up Continuous Integration
---------------------------------

Obviously, in the step above, you developed a robust suite of unit
tests, likely using [Mocha](http://mochajs.org/)and
[Should](https://github.com/shouldjs/should.js).  Now you should turn
those tests into a continuous integration step via
[Travis](http://travis-ci.org/)(free for OSS projects).  Simply [go
there](http://travis-ci.org/)and sign in via GitHub - your repositories
will show up and you'll be able to turn on the ones you want.  You can
easily set up a `.travis.yml` file in your repository to guide the CI
build - here's a simple one for my project that uses the `npm test` step
to perform the linting and testing:

```yaml
language: node_js

node_js:
  - "0.12"
  - "0.10"

cache:
  directories:
    - node_modules

script:
  - npm test
```

Since this was a simple module, npm was adequate for my build/test needs
and I didn't need to resort to gulp or grunt (Keith Cirkel [has some
info](http://blog.keithcirkel.co.uk/how-to-use-npm-as-a-build-tool/)on
the how's and why's for that decision - I'm not totally bought-in, but
for simple projects it makes sense).  My package.json to make that
happen looks like:

```js
...
  "devDependencies": {
    "jshint": "^2.5.11",
    "mocha": "^1.21.4",
    "should": "^4.0.4"
  },
  "scripts": {
    "pretest": "jshint lib",
    "test": "mocha test"
  }
...
```

Now you can rest assured that Travis is building your code on every
push, and you can advertise that fact in your readme.  I also use the
[David dependency manager](https://david-dm.org/) to ensure that my
dependencies don't swing too far out of date, and advertise that as
well.  Adding these to your README.md is as simple as (replacing *user*
and *module* as appropriate):

```markdown
[![Build Status](https://secure.travis-ci.org/user/module.png?branch=master)](https://travis-ci.org/user/module)
[![Dependency Status](https://david-dm.org/user/module.png)](https://david-dm.org/user/module)
```

Publishing to NPM
-----------------

Once you've developed your amazing Node.js module, you'll want to
publish it for all the world to see.  To do so, you use `npm publish`,
but beware.  Read[their developer
guide](https://docs.npmjs.com/misc/developers "NPM Developer Guide"),
and be careful to note *this phrase*:

> Note that pretty much **everything in that folder will be exposed** by
> default.

When I first published my module, I failed to note that phrase, and
published log files, the .idea folder, and a bunch of other garbage.
 Since I'm paranoid, the way I manage this now is to have a shadow
directory side-by-side with my development folder called "publish" - I
`git clone/git pull` into that when I'm ready to publish, bump the
versions from there, and `npm publish` with confidence.

Working With Others
-------------------

You've forked someone's project, worked on it, and now want to ensure
that you're up to date with their branch.  GitHub has some [great
documentation](https://help.github.com/articles/syncing-a-fork/ "Syncing a Fork on GitHub")
on how to make sure you've merged their latest changes - basically you
need to ensure you've mapped the upstream remote, and then fetch it and
merge it:

```bash
git remote add upstream https://github.com/my/clone/uri
git fetch upstream
git merge upstream/master
git push
```

If you run into any merge issues, [this StackOverflow
post](http://stackoverflow.com/questions/161813/fix-merge-conflicts-in-git "Fixing Merge Conflicts")
has some advice, and there are some decent merge tools out there.  I
recommend Beyond Compare if you have the scratch, but otherwise
[kdiff3](http://kdiff3.sourceforge.net/)runs on just about everything.

When others submit pull requests to your module, you'll get notified by
GitHub and can then go deal with the PRs.  For example, I've submitted
this change to `node-sbus` from my fork to the originator.  Since I'm a
contributor on the upstream repo, the view I see when I go to the Pull
Requests tab on that repo looks like:

![merge\_pr]({filename}/images/merge_pr.png)

Note that I can automatically merge this PR, but since I have Travis set
up it's telling me that it hasn't yet passed the build.  I should wait
until I get a green light on that before considering accepting the PR -
in the meantime I can click on the one change to go to a diff view and
review it:

![pr\_diff]({filename}/images/pr_diff_sm.png)

Looks good to me, and the Travis build has now passed (not strictly
necessary since this was just a content change), so I accept the PR.

 Multiple Owners, Multiple Publishers
-------------------------------------

Now someone has forked your module, proved themselves, and you want to
add them as a collaborator.  You'll need to add them in both GitHub and
NPM in order to make them a full peer for pushing/handling PRs and
publishing.  For GitHub, you'll add them as a collaborator to your
project using Settings-\>Collaborators:

![github\_collaborators]({filename}/images/github_collaborators.png)

And for NPM you'll need to [add the user as an
owner](https://docs.npmjs.com/cli/owner "NPM Owner").  This should allow
both of you to push changes, integrate pull requests, and publish new
versions.

Hopefully this has been helpful - let me know if I've missed any basics,
and if you have any other suggestions or ideas for collaborating on OSS
projects.

