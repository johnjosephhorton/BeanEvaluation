from google.appengine.ext import db as datastore


class Worker(datastore.Model):
  created = datastore.DateTimeProperty(auto_now_add=True)
  creator = datastore.UserProperty()
  access_token = datastore.StringProperty()
  odesk_identifier = datastore.StringProperty()
  email_address = datastore.EmailProperty()
  name = datastore.StringProperty()

class Bucket(datastore.Model):
  created = datastore.DateTimeProperty(auto_now_add=True)
  creator = datastore.UserProperty()
  name = datastore.StringProperty()

class Image(datastore.Model):
  bucket = datastore.ReferenceProperty(Bucket, collection_name='images')
  url = datastore.StringProperty()
