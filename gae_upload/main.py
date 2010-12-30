from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app as run_wsgi

from beaneval.http import RequestHandler


class Root(RequestHandler):
  def get(self):
    self.write('ok')


def handlers():
  return [
    ('/', Root)
  ]


def application():
  return webapp.WSGIApplication(handlers(), debug=True)


def main():
  run_wsgi(application())


if __name__ == '__main__':
  main()
