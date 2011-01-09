from google.appengine.ext import db as datastore

from datetime import datetime


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
  import_started = datastore.DateTimeProperty()
  import_finished = datastore.DateTimeProperty()


class Image(datastore.Model):
  bucket = datastore.ReferenceProperty(Bucket, collection_name='images')
  url = datastore.StringProperty()


class Evaluation(datastore.Model):
  created = datastore.DateTimeProperty(auto_now_add=True)
  worker = datastore.ReferenceProperty(Worker, collection_name='evaluations')
  image = datastore.ReferenceProperty(Image, collection_name='evaluations')
  tape_id = datastore.IntegerProperty()
  day = datastore.IntegerProperty()
  month = datastore.IntegerProperty()
  error_count = datastore.IntegerProperty()


def start_import(bucket_key):
  return datastore.run_in_transaction(_set_import_started, bucket_key)


def _set_import_started(bucket_key):
  bucket = datastore.get(bucket_key)

  if bucket.import_started:
    return None

  bucket.import_started = datetime.now()
  bucket.put()

  return bucket
