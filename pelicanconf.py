#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Mike Lanzetta'
SITENAME = 'Intelligent Artifice'
SITEURL = ''

TIMEZONE = 'America/Tijuana'
DEFAULT_LANG = 'en'

PATH = 'content'

STATIC_PATHS = ['images', 'extra/robots.txt', 'extra/favicon.ico']
EXTRA_PATH_METADATA = {
    'extra/robots.txt': {'path': 'robots.txt'},
    'extra/favicon.ico': {'path': 'favicon.ico'}
}

# Plugin Settings
SITEMAP = { 'format': 'xml' }

# Plugin Usage
PLUGIN_PATHS = ['../pelican-plugins']
PLUGINS = ['sitemap', 'gravatar']

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Cortana Analytics', 'https://blogs.technet.microsoft.com/machinelearning/'),
         ('KDNuggets', 'http://www.kdnuggets.com/'),
         ('Hanselman', 'http://www.hanselman.com/blog/'))

# Social widget
DEFAULT_PAGINATION = False

DISQUS_SITENAME = 'intelligentartifice'
GITHUB_URL = 'https://github.com/noodlefrenzy'
GOOGLE_ANALYTICS = 'UA-54597100-1'
SOCIAL = (('Twitter', 'https://twitter.com/noodlefrenzy'),
          ('LinkedIn', 'https://www.linkedin.com/in/noodlefrenzy'),)

TWITTER_USERNAME = 'noodlefrenzy'

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
