# -*- coding: utf-8 -*-
import ConfigParser
from ConfigParser import SafeConfigParser
import sys
import pkg_resources
import requests
from flask import Flask, request, Response
import pprint
import json

from achlib.util import logger
from achlib.util.dbutil import db_fetch, db_insup

app = Flask(__name__)
log = logger.getLogger(__name__)
config_local = SafeConfigParser()
config_local.readfp(pkg_resources.resource_stream(__name__, "config-local.ini"))

@app.route('/', methods=['GET'])
def verify():
    log.info('checking service health')
    return 'service is up'


@app.route('/', methods=['POST'])
def donate_item():
    pass

def pretty_print_POST(req):
    """
    This method takes a request and print
    """
    log.info('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        '\n'.join('{}: {}'.format(k, v) for k, v in req.args.to_dict().items()),
    ))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
