# IntelligentArtifice

Developer blog of Mike Lanzetta

# Deployment

This blog was created via Pelican. In order to deploy your own version, you can use the same procedure I've used:

1) Download and install [Pelican](http://blog.getpelican.com/) - `pip install pelican` (I'd also recommend installing markdown).
1) Download and install [ghp-import](https://github.com/davisp/ghp-import) - see [the Pelican docs](http://docs.getpelican.com/en/3.6.3/tips.html#publishing-to-github) for details.
1) run `pelican content` to turn the `content` directory into the `output` directory.
1) set up the remote for your GitHub where you want the pages to be deployed
