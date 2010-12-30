from google.appengine.ext import db as datastore


class Worker(datastore.Model):
  created = datastore.DateTimeProperty(auto_now_add=True)
  creator = datastore.UserProperty()
  access_token = datastore.StringProperty()
  last_seen = datastore.DateTimeProperty()
  odesk_identifier = datastore.StringProperty()
  email_address = datastore.EmailProperty()
  name = datastore.StringProperty()


class Bucket(datastore.Model):
  created = datastore.DateTimeProperty(auto_now_add=True)
  creator = datastore.UserProperty()


class Image(datastore.Model):
  bucket = datastore.ReferenceProperty(Bucket, collection_name='images')
  url = datastore.StringProperty()
