from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run_wsgi

from beaneval.http import RequestHandler
from beaneval.models import Worker
from beaneval.misc import nonce


class Root(RequestHandler):
  def get(self):
    self.write('ok')


class WorkerForm(RequestHandler):
  def get(self):
    self.render('priv/worker_form.html', {
      'self': self
    , 'worker': Worker()
    })

  def post(self):
    worker = Worker()
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


class EvaluationForm(RequestHandler):
  def get(self, access_token):
    worker = Worker.all().filter('access_token =', access_token).get()

    if worker is None:
      pass
    else:
      self.write('TODO')


def handlers():
  return [
    ('/', Root)
  , ('/worker', WorkerForm)
  , ('/evaluation/([^/]+)', EvaluationForm)
  ]


def application():
  return webapp.WSGIApplication(handlers(), debug=True)


def main():
  run_wsgi(application())


if __name__ == '__main__':
  main()
