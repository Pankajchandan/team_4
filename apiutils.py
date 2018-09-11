import ConfigParser
from ConfigParser import SafeConfigParser
import sys
import pkg_resources
import json

import requests

import templates
from achlib.util import logger

log = logger.getLogger(__name__)
config_local = SafeConfigParser()
config_local.readfp(pkg_resources.resource_stream(__name__, "config-local.ini"))


def is_disaster(wind_speed):
    wind_check = [int(i) for i in config_local.get\
    ('PARAMETERS','wind_check').split(',')]
    log.info("wind_speed: {}\nwind_check:{}".format(wind_speed,wind_check))
    if not wind_speed:
        return -1
    for i, check in enumerate(wind_check):
        if wind_speed<check:
            return i

    return 5


def get_weather_forecast(url):
    api_key = config_local.get('KEYS','forecast_api_key')
    lines = [line.rstrip('\n') for line in open('data/uscitiesv1.4.dat')]
    weather_result = []
    # content = requests.get(url).json()
    keys = ["Keys", "Miami", "Augustine", "Island", "Jacksonville", "Naples"]
    for l in lines:
        info = l.strip().split(",")
        if "Florida" in info[3] and any(key in info[0] for key in keys):
            city = info[0]
            county_fips = info[4]
            county_name = info[5]
            lat = info[6]
            lng = info[7]
            zips = info[14]
            url_option = "?lat="+lat+"&lon="+lng+"&appid="+api_key
            api_url = url+url_option
            data = requests.get(api_url).json()
            data["county_fips"] = county_fips[3:-1]
            data["county_name"] = county_name
            data["zips"] = zips
            weather_result.append(data)
            #print(json.dumps(data, indent=4, sort_keys=True))
        else:
            continue

    return weather_result


def find_disaster(weather_result):
    result=dict()
    for weather in weather_result:
        disaster_type = config_local.get('PARAMETERS','disaster_type')
        disaster_level = 0
        for items in weather["list"]:
            date = items["dt_txt"]
            pressure = items["main"]["pressure"]
            temp = items["main"]["temp"]
            wind_speed = items["wind"]["speed"]
            disaster_level = max(disaster_level,is_disaster(items["wind"]["speed"]))
        if disaster_level <=0:
            continue
        url = config_local.get('URL','api_endpoint').\
        format(weather["county_fips"],config_local.get('KEYS','wether_api_key'))
        log.debug("find_disaster url = {}".format(url))
        response = requests.get(api).text[37:-2].split(",")
        log.info("response from find_disaster api : {}".format(response))

        population = response[0].replace('\"','').replace('[','')
        final_result = {}
        final_result["disaster_type"] = disaster_type
        final_result["disaster_level"] = disaster_level
        final_result["date"] = date
        final_result["temp"] = temp
        final_result["wind_speed"] = wind_speed
        final_result["lat"] = weather["city"]["coord"]["lat"]
        final_result["lon"] = weather["city"]["coord"]["lon"]
        final_result["fips"] = weather["county_fips"]
        final_result["population"] = population
        final_result["county_name"] = weather["county_name"].strip("\"")
        final_result["zips"] = weather["zips"]
        final_result["state"] = "florida"
        result[fips] = final_result

    return result


def main():
    disaster = find_disaster(get_weather_forecast\
    (config_local.get('URL','wether_host'))
    log.info((json.dumps(disaster,indent=4,sort_keys=True)))


if __name__ == '__main__':
    main()
