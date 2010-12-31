from google.appengine.api import users
from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run_wsgi

from beaneval.http import RequestHandler
from beaneval.models import Worker, Bucket, Image
from beaneval.models import start_import
from beaneval.misc import nonce
from beaneval import s3

from datetime import datetime


class Dashboard(RequestHandler):
  def get(self):
    self.render('priv/dashboard.html', {
      'worker_count': Worker.all().count()
    , 'bucket_count': Bucket.all().count()
    , 'image_count': Image.all().count()
    , 'worker_form_url': self.host_url('/worker')
    , 'bucket_form_url': self.host_url('/bucket')
    })


class WorkerForm(RequestHandler):
  def get(self):
    self.render('priv/worker_form.html', {
      'self': self
    , 'worker': Worker()
    })

  def post(self):
    worker = Worker()
    worker.creator = users.get_current_user()
    worker.access_token = nonce()
    worker.odesk_identifier = self.param_value('odesk_identifier')
    worker.email_address = self.param_value('email_address')
    worker.name = self.param_value('name')
    worker.put()

    access_url = self.host_url('/evaluation/%s' % worker.access_token)

    self.render('priv/worker_access_url.html', {
      'worker': worker
    , 'access_url': access_url
    })


class BucketForm(RequestHandler):
  def get(self):
    self.render('priv/bucket_form.html', {'self': self})

  def post(self):
    bucket_name = self.param_value('name')

    if bucket_name:
      if s3.bucket_exists(bucket_name):
        if Bucket.get_by_key_name(bucket_name):
          self.bad_request('Error: bucket already imported')
        else:
          bucket = Bucket(key_name=bucket_name)
          bucket.creator = users.get_current_user()
          bucket.put()

          taskqueue.add(queue_name='bucket-import', params={'key': bucket.key()})

          self.write('ACCEPTED') # TODO: redirect to status page
      else:
        self.bad_request('Error: "%s" bucket does not exist' % bucket_name)
    else:
      self.redirect(self.request.url)


class BucketImportTask(RequestHandler):
  def post(self):
    bucket = start_import(self.request.get('key'))

    if bucket:
      bucket_name = bucket.key().name()

      for key in s3.bucket_lookup(bucket_name).list():
        image = Image()
        image.bucket = bucket
        image.url = 'http://%s.s3.amazonaws.com/%s' % (bucket_name, key.name)
        image.put()

      bucket.import_finished = datetime.now()
      bucket.put()


class EvaluationForm(RequestHandler):
  def get(self, access_token):
    worker = Worker.all().filter('access_token =', access_token).get()

    if worker is None:
      pass
    else:
      worker.last_seen = datetime.now()
      worker.put()

      self.write('TODO')


def handlers():
  return [
    ('/', Dashboard)
  , ('/_ah/queue/bucket-import', BucketImportTask)
  , ('/worker', WorkerForm)
  , ('/bucket', BucketForm)
  , ('/evaluation/([^/]+)', EvaluationForm)
  ]


def application():
  return webapp.WSGIApplication(handlers(), debug=True)


def main():
  run_wsgi(application())


if __name__ == '__main__':
  main()
