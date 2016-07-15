Title: Running Azure Mobile Services Locally
Date: 2014-09-08 11:32
Author: noodlefrenzy
Category: Software
Tags: Azure, Mobile, Node
Slug: running-azure-mobile-services-locally
Status: published

On a recent project, I made my first foray into using Azure Mobile
Services [Custom
API](http://weblogs.asp.net/scottgu/windows-azure-major-updates-for-mobile-backend-development "Azure Custom API Announcement")
support, with a Node.js-backed API implementation.  I've used (and
loved) Mobile Services in the past for their push notification
infrastructure, but this was new ground for me.  I liked the easy
setup - trivial to create a new API method and write code, in the
browser, to implement it - but once your API implementation went beyond
"toy" it quickly became unmanageable.

They have integrated
Git support which allows you to locally clone your API code (see the
Configure tab for the Git URL), modify it, and then push changes which
will cause an auto-deployment. This works great, but the problem is that
you can't run *or *test those changes locally before deployment,
and that's not the kind of test-in-production workflow I'm into.

![I don't always test my code, but when I do, I do it in production.]({filename}/images/test_in_production.jpg)

I talked with the Azure Mobile Services team about their testing story,
and was told that they'd been focusing on improving the .NET-backed
services first - they would love to get Node.js local development fixed
and realized it was a gap, but just didn't have the resources right now.
 I didn't want to wait, so decided I would fix it myself.

#### My Solution

I've implemented a lightweight
local [Expressjs](http://expressjs.com/ "ExpressJs Home") server that
runs locally, interrogates all .js files in your API directory to
determine which methods are implemented, and registers those paths.
 This allowed me to run locally, and I was easily able to extend it to
handle the "register" method to support additional custom API paths.  I
then included a simple example unit-test that uses
[Mocha](http://visionmedia.github.io/mocha/ "Mocha Home")to run the
tests (heavily indebted to [51 Elliot's
post](http://51elliot.blogspot.com/2013/08/testing-expressjs-rest-api-with-mocha.html "Expressjs Testing With Mocha")[ ](http://51elliot.blogspot.com/2013/08/testing-expressjs-rest-api-with-mocha.html)for
helping me out here), starting up the local Expressjs and hitting the
API methods as needed.  I've checked all of this into GitHub so others
can use it and extend it as they see
fit: <https://github.com/noodlefrenzy/azure-mobile-local>.

This code depends on a few pieces of software, so you should make sure
you've installed
[Git](https://help.github.com/articles/set-up-git "Setting Up Git"),
[Node.js](http://nodejs.org/) (and **npm** is in your path), and then
install the Grunt CLI and Mocha before starting.  Technically, you
don't *need* to install Mocha as you can use it just fine from Grunt and
the dev dependency, but it's too useful not to just have it on your path
(the first time you run `mocha debug` you'll agree with me).

```bash
npm install -g grunt-cli
npm install -g mocha
```

The simplest way to use it (and I'm indebted to my colleague [Jason
Poon](http://jasonpoon.ca) for this) is to mount it as a [git
submodule](http://git-scm.com/docs/git-submodule "Git Submodule Documentation")
of your Azure Mobile Service git repository.  This allows both
code-bases to peacefully co-exist, and ensures pushing changes to tests
or the local server don't trigger deployments of your service.  Setting
this up is simple:

```bash
git clone _your azure mobile service git URL_
cd _directory from above_
git submodule add https://github.com/noodlefrenzy/azure-mobile-local.git local
cd local
npm install
grunt build
```

When you `grunt build`, this runs
[Jshint](http://www.jshint.com/ "JSHint Home")against your API, and any
unit-tests in the `local/test/**/*.js` files.

#### Simple Example

For instance, with my simple example mobile service below:

```js
exports.post = function(request, response) {
    response.send(200, { message : 'Hello World!' });
};

exports.get = function(request, response) {
    response.send(200, { message : 'Hello World!' });
};

exports.register = function(api) {
    api.get('/mycustom', myCustomMethod);
};

function myCustomMethod(request, response) {
    response.send(200, { message : 'Hello from custom routing!' });
}
```

I've written the following unit-tests that simply test whether the paths
that I've registered resolve, and return 200s when called:

```js
var should = require('should');
var app = require('../server.js').app;
var port = 4321;
var http = require('http');

function defaultGetOptions(path) {
  var options = {
    "host": "localhost",
    "port": port,
    "path": path,
    "method": "GET",
  };
  return options;
}

describe('app', function () {
 
  before (function (done) {
    //debugger;
    app.listen(port, function (err, result) {
      if (err) {
        done(err);
      } else {
        done();
      }
    });
  });
 
  after(function (done) {
    //app.close();
    done();
  });
 
  it('should be created', function (done) {
    should.exist(app);
    done();
  });
 
  it('should be listening', function (done) {
    var headers = defaultGetOptions('/');
    http.get(headers, function (res) {
      res.statusCode.should.eql(404);
      done();
    });
  });

  it('should have myendpoint api route', function (done) {
    var headers = defaultGetOptions('/api/myendpoint');
    http.get(headers, function(res) {
      res.statusCode.should.eql(200);
      done();
    });
  });

  it('should have myendpoint/mycustom api route', function (done) {
    var headers = defaultGetOptions('/api/myendpoint/mycustom');
    http.get(headers, function(res) {
      res.statusCode.should.eql(200);
      done();
    });
  });
 
});
```

These tests can be extended arbitrarily, and with a simple change to the
Gruntfile.js:

```js
  simplemocha: {
      options: {
        globals: ['should'],
        timeout: 3000,
        ignoreLeaks: false,
        ui: 'bdd',
        reporter: 'list',
      },
      all: { src: ['test/**/*.js', '../test/**/*.js'] }
  },
```

You can instead add your own `test/` directory to your mobile service
and have your tests live in the same place as the service itself (a much
better answer, but harder to demo for me).

#### Further Work and Caveats

All I needed for my project was a simple API (I was passing through to
some services on other VMs), so I didn't implement mocks for any of the
Azure services that get included with Mobile Services (e.g. the Table
abstraction).  I also didn't inject the mysterious statusCodes enum that
gets included automagically in your APIs, and instead just replaced them
with 200s.

As mentioned above, the code is all in GitHub right here:
<https://github.com/noodlefrenzy/azure-mobile-local> - if you see
obvious improvements, I'd love to hear about them either in comments or
pull requests.

