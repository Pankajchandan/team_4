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
import templates

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
        deficit = int(res[4])
        if deficit > 0:
            line_items[res[2]] = int(res[4])
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
    #pretty_print_POST(request)
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
    #log.info("doner_addresses: {}".format(doner_addr))
    for add in doner_addr:
        lat = add[0].split(',')[0]
        lng = add[0].split(',')[1]
        if lat_bound_low <= float(lat) <= lat_bound_high and lng_bound_low <= float(lng) <= lng_bound_high:
            log.info("nearby doner lat: {}, long: {}".format(lat, lng))
            log.info("bounds: {},{},{},{}".format(lat_bound_low, lat_bound_high,lng_bound_low, lng_bound_high))
            statement = "select name, address, phone from users_hack where id='{}'".format(res[2])
            log.info("fetch statement: {}".format(statement))
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
    upd_qty = {}
    for key, val in dict(pickups).items():
        statement = "select resource_id, quantity from procurement where donor_id='{}' and status='N'".format(val)
        result = db_fetch(statement)
        statement = "update procurement set status='P' where donor_id='{}'".format(val)
        db_insup(statement)
        for res in result:
            if res[0] not in upd_qty:
                upd_qty[res[0]] = int(res[1])
            else:
                upd_qty[res[0]] += int(res[1])
    update_procurement(upd_qty)
    return Response(json.dumps(resp), headers=HEADER, status=200, mimetype='application/json')



@app.route('/compute_resource', methods=['OPTIONS','POST'])
def compute_resource():
    ''' Computes required resources based on calamity and required resources'''
    content = request.json
    disaster_type = content['disaster_type']
    category = content['category']
    population = int(content['population'])
    items = templates.resource_requirements[disaster_type][category]["items"]
    recovery_time = templates.resource_requirements[disaster_type][category]["recovery_time"]
    required_items = {}
    for item, qty in items.iteritems():
        required_items[item] = int(population * qty * recovery_time)
        log.info("required_items: {}".format(required_items[item]))
    query = "select name, deficit, current_inventory, storage_id from resource where name in ("+str(
        items.keys())[1:-1:]+") and storage_id = '1'"
    log.info("compite_resource_query_fetch: {}".format(query))
    result = db_fetch(query)
    for row in result:
        if(required_items[row[0]] < row[2]):
            query = "update resource set deficit=" + \
                str(int(row[2]) + required_items[row[0]]) + \
                " where name='" + row[0] + "';"
            log.info("compute_resource_query_insup: {}".format(query))
            db_insup(query)
    resp = {"msg": "OK"}

    return Response(json.dumps(resp), headers=HEADER, status=200, mimetype='application/json')


def update_procurement(upd_qty):
    log.info("upd_qty = {}".format(upd_qty))
    for resource_id, qty in upd_qty.items():
        statement = "select current_inventory, deficit from resource where id='{}'".format(resource_id)
        res = db_fetch(statement)
        current_inventory = str(int(res[0][0])+qty)
        deficit = str(int(res[0][1])-qty)
        statement = "update resource set current_inventory='{}', deficit='{}' where id='{}'"\
        .format(current_inventory,deficit,resource_id)
        log.info("update statement: {}".format(statement))
        db_insup(statement)


def insert_procurement(doner_id, addr, items):
    log.info("in update function {}, {}, {}".format(doner_id, addr, items))
    for key, val in items.items():
        statement = "select id from resource where name='{}'".format(key)
        result = db_fetch(statement)
        if result:
            resource_id = result[0][0]
            #log.info("addr = {}".format(addr))
            coordinate = str(addr['lat']) + "," + str(addr['lng'])
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
    app.run(host='0.0.0.0', debug=True, port='8080')
