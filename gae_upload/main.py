from google.appengine.api import users
from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run_wsgi

from beaneval.http import RequestHandler
from beaneval.http import access_token_required
from beaneval.models import Worker, Bucket, Image, Evaluation
from beaneval.models import start_import, next_image
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

          self.redirect('/')
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
  @access_token_required
  def get(self, access_token):
    if self.worker.bucket:
      if self.worker.image:
        self.render('priv/evaluation_form.html', {
          'self': self
        , 'image_url': self.worker.image.url
        })
      else:
        self.write('No images to evaluate')
    else:
      self.write('No images to evaluate')

  @access_token_required
  def post(self, access_token):
    if self.worker.image:
      evaluation = Evaluation()

      try:
        evaluation.tape_id = int(self.request.get('tape_id'))
        evaluation.day = int(self.request.get('day'))
        evaluation.month = int(self.request.get('month'))
        evaluation.error_count = int(self.request.get('error_count'))
      except ValueError:
        return self.bad_request()

      evaluation.worker = self.worker
      evaluation.image = self.worker.image
      evaluation.put()

      self.worker.image = next_image(self.worker)
      self.worker.put()

      self.redirect(self.request.url)
    else:
      self.method_not_allowed()


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
