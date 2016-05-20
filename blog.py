import os
import re
import codecs
import hashlib
import hmac
import random
import string
import webapp2
import jinja2

from users import *

from google.appengine.ext import ndb

def blog_key(name = 'default'):
    return ndb.Key('blogs', name)

class BlogPost(ndb.Model):
    subject = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    created = ndb.DateTimeProperty(auto_now_add = True)
    author = ndb.StructuredProperty(User)
