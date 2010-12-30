from boto.s3.connection import S3Connection

import yaml


def connection():
  aws = load_yaml('aws.yaml')

  return S3Connection(aws['access_key_id'], aws['secret_access_key'])


def bucket_exists(bucket_name):
  return bool(connection().lookup(bucket_name))


def load_yaml(path):
  io = open(path)

  data = yaml.load(io)

  io.close()

  return data
