# -*- coding: utf-8 -*-
import ConfigParser
from ConfigParser import SafeConfigParser
import sys
import pkg_resources
from flask import Flask, request, Response
from flask_cors import CORS
import pprint
import json

import requests
import googlemaps

from achlib.util import logger
from achlib.util.dbutil import db_fetch, db_insup

app = Flask(__name__)
CORS(app)
log = logger.getLogger(__name__)
config_local = SafeConfigParser()
config_local.readfp(pkg_resources.resource_stream(__name__, "config-local.ini"))

gmaps = googlemaps.Client(key=config_local.get('MAPS','key'))
HEADER = {'Access-Control-Allow-Origin': '*'}

@app.route('/', methods=['GET'])
def verify():
    log.info('checking service health')
    return 'service is up'


@app.route('/get_items', methods=['GET'])
def get_items():
    statement = "select * from resource"
    log.info('query:  {}'.format(statement))
    result = db_fetch(statement)
    log.info(result)
    send_data = {
      u"items": {}
      }
    line_items = dict()
    for res in result:
        deficit = int(res[4])-int(res[3])
        if deficit > 0:
            line_items[res[2]] = int(res[4])-int(res[3])
    send_data['items'] = line_items
    return Response(json.dumps(send_data), headers=HEADER, status=200, mimetype='application/json')



@app.route('/donate_item', methods=['OPTIONS','POST'])
def donate_item():
    try:
        content = request.json
        log.info("item to donate: {}".format(content))
        statement = "select id, address from users_hack where name='{}'".format(content['d_name'])
        result = db_fetch(statement)
        if result:
            id = result[0][0]
            address = result[0][0]
        else:
            raise ValueError('No ID found for {}'.format(content['d_name']))
        geocode_result = gmaps.geocode(content['addr'])[0]['geometry']['location']
        insert_procurement(id, geocode_result, content['items'])
        resp = {u"message": u"Thank you for the good gesture"}
        return Response(json.dumps(resp), headers=HEADER, status=200, mimetype='application/json')
    except Exception as e:
        resp = {u"message": u"could not make request...{}".format(e)}
        raise
    finally:
        #return Response(json.dumps(resp), status=500, mimetype='application/json')
        pass


@app.route('/driver_see_pickups', methods=['POST','OPTIONS'])
def driver_see_pickups():
    pretty_print_POST(request)
    if not request.json:
        return 'OK'
    print request.json
    driver_addr = request.json['addr']
    geocode_result = gmaps.geocode(driver_addr)[0]['geometry']['location']
    log.info("driver address {}".format(geocode_result))
    lat_bound_low, lat_bound_high = geocode_result['lat'] - 0.05, geocode_result['lat'] + 0.05
    lng_bound_low, lng_bound_high = geocode_result['lng'] - 0.05, geocode_result['lng'] + 0.05
    statement = "select * from procurement where status='N'"
    result = db_fetch(statement)
    counter, resp = 1, {}
    doner_addr = set()
    for res in result:
        doner_addr.add((res[6],res[2]))
    print doner_addr
    for add in doner_addr:
        lat = add[0].split(',')[0]
        lng = add[0].split(',')[1]
        log.info("lat: {}, long: {}".format(lat, lng))
        log.info("bounds: {},{},{},{}".format(lat_bound_low, lat_bound_high,lng_bound_low, lng_bound_high))
        if lat_bound_low <= float(lat) <= lat_bound_high and lng_bound_low <= float(lng) <= lng_bound_high:
            statement = "select name, address, phone from users_hack where id='{}'".format(res[2])
            doner_info= db_fetch(statement)
            resp['coord_{}'.format(counter)] = {}
            resp['coord_{}'.format(counter)]['d_id'] = res[2]
            resp['coord_{}'.format(counter)]['lat'] = lat
            resp['coord_{}'.format(counter)]['lng'] = lng
            resp['coord_{}'.format(counter)]['name'] = doner_info[0][0]
            resp['coord_{}'.format(counter)]['addr'] = doner_info[0][1]
            resp['coord_{}'.format(counter)]['phone'] = doner_info[0][2]
            counter += 1

    return Response(json.dumps(resp), headers=HEADER, status=200, mimetype='application/json')



@app.route('/pickup_item', methods=['OPTIONS','POST'])
def pickup_item():
    resp = {"msg": "OK"}
    pickups = request.json
    print pickups
    for key, val in dict(pickups).items():
        statement = "update procurement set status='P' where donor_id='{}'".format(val)
        db_insup(statement)
        statement = "select resource_id, quantity from procurement where donor_id='{}'".format(val)
        result = db_fetch(statement)
        for res in result:
            log.info("result fetched in pickup_items: {}".format(res))

    return Response(json.dumps(resp), headers=HEADER, status=200, mimetype='application/json')


def update_procurement(doner_id, addr, items):
    pass


def insert_procurement(doner_id, addr, items):
    log.info("in update function {}, {}, {}".format(doner_id, addr, items))
    for key, val in items.items():
        statement = "select id from resource where name='{}'".format(key)
        result = db_fetch(statement)
        if result:
            resource_id = result[0][0]
            coordinate = ""
            for key1, val1 in addr.items():
                coordinate += str(val1)+","
            coordinate = coordinate[:-1]
            #print str(resource_id), str(val), coordinate
            statement = "INSERT INTO public.procurement (resource_id, quantity, donor_id, coordinate, status) \
            VALUES('{}','{}','{}','{}','{}')".format(resource_id,str(val),doner_id, coordinate, 'N')
            log.info("statement to execute: {}".format(statement))
            db_insup(statement)
        else:
            raise ValueError('No result found for {}'.format(key))



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
