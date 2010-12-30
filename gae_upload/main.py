from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run_wsgi

from beaneval.http import RequestHandler
from beaneval.models import Worker, Bucket
from beaneval.misc import nonce

from boto.s3.connection import S3Connection

import yaml


class Dashboard(RequestHandler):
  def get(self):
    self.render('priv/dashboard.html', {
      'worker_count': Worker.all().count()
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
      if self._bucket_exists(bucket_name):
        bucket = Bucket()
        bucket.creator = users.get_current_user()
        bucket.name = bucket_name
        bucket.put()

        # TODO: enqueue BucketImportTask

        self.write('ACCEPTED') # TODO: redirect to status page
      else:
        self.bad_request('Error: "%s" bucket does not exist' % bucket_name)
    else:
      self.redirect(self.request.url)

  def _bucket_exists(self, bucket_name):
    aws = self._load_yaml('aws.yaml')

    connection = S3Connection(aws['access_key_id'], aws['secret_access_key'])

    return bool(connection.lookup(bucket_name))

  def _load_yaml(self, path):
    io = open(path)

    data = yaml.load(io)

    io.close()

    return data


class EvaluationForm(RequestHandler):
  def get(self, access_token):
    worker = Worker.all().filter('access_token =', access_token).get()

    if worker is None:
      pass
    else:
      self.write('TODO')


def handlers():
  return [
    ('/', Dashboard)
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
