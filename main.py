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
from blog import *

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **kw):
        t = jinja_env.get_template(template)
        return t.render(kw)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainHandler(Handler):
    def get(self):
        self.render("index.html")

class Rot13Handler(Handler):
    def get(self):
        self.render("rot13.html")

    def post(self):
        text = self.request.get("text")
        if text:
            text = codecs.encode(text, 'rot_13')
        self.render('rot13.html', text = text)

class SignupHandler(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        user_error = False
        pwd_error = False
        verify_error = False
        email_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        if not username or not users.valid_username(username):
            user_error = True
        if not password or not verify or not users.valid_password(password):
            pwd_error = True
        if password != verify:
            verify_error = True
        if email and not users.valid_email(email):
            email_error = True

        if user_error or pwd_error or verify_error or email_error:
            self.render("signup.html", user_error = user_error,
                                       pwd_error = pwd_error,
                                       verify_error = verify_error,
                                       email_error = email_error,
                                       username = username,
                                       email = email)
        else:
            user = User(username = username, pwd_hash = users.make_pw_hash(username, password), email = email)
            user.put()
            user_cookie = users.make_secure_val(str(username))
            self.response.headers.add_header("Set-Cookie", "user=%s; Path=/" % user_cookie)
            self.redirect("/welcome")

class WelcomeHandler(Handler):
    def get(self):
        user = self.request.cookies.get('user')
        if user:
            username = users.check_secure_val(user)
            if username:
                self.render("welcome.html", username = username)
            else:
                self.redirect('/signup')
        else:
            self.redirect('/signup')

class LoginHandler(Handler):
    def get(self):
        self.render("login.html")
    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        user = db.GqlQuery("SELECT * FROM User WHERE username = '%s'" % username)[0]
        if users.valid_pw(username, password, user.pwd_hash):
            user_cookie = users.make_secure_val(str(username))
            self.response.headers.add_header("Set-Cookie", "user=%s; Path=/" % user_cookie)
            self.redirect("/welcome")
        else:
            self.render("login.html")

class LogoutHandler(Handler):
    def get(self):
        self.response.headers.add_header("Set-Cookie", "user=; Path=/")
        self.redirect("/signup")

class BlogHandler(Handler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
        self.render("blog.html", posts = posts)

class NewPostHandler(Handler):
    def get(self):
        self.render("newpost.html")
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content:
            post = BlogPost(parent = blog_key(), subject = subject, content = content)
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))
        else:
            error = "you need both a subject and content"
            self.render("newpost.html", subject = subject, content = content, error = error)

class PostHandler(Handler):
    def get(self, post_id):
        key = db.Key.from_path('BlogPost', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        self.render("blogpost.html", post = post)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/rot13', Rot13Handler),
    ('/signup', SignupHandler),
    ('/welcome', WelcomeHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/blog', BlogHandler),
    ('/blog/newpost', NewPostHandler),
    ('/blog/([0-9]+)', PostHandler)
], debug=True)
