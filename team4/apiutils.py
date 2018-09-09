import requests
import json

# wind speed are in m/s
def isDisaster(pressure, wind_speed):
    if not wind_speed:
        return -1
    if wind_speed < 6: #34
        return 0
    if wind_speed < 7: #43
        return 1
    if wind_speed < 50:
        return 2
    if wind_speed < 58:
        return 3
    if wind_speed < 70:
        return 4

    return 5


def findDisaster(weather_result):

    result={}
    for weather in weather_result:
        disaster_type = "hurricane"
        disaster_level = 0
        list = weather["list"]
        for items in list:

            date = items["dt_txt"]
            pressure = items["main"]["pressure"]
            temp = items["main"]["temp"]
            wind_speed = items["wind"]["speed"]
            if isDisaster(pressure, wind_speed) > disaster_level:
                disaster_level = isDisaster(pressure, wind_speed)
        if disaster_level <=0:
            continue

        lat =  weather["city"]["coord"]["lat"]
        lon = weather["city"]["coord"]["lon"]
        fips = weather["county_fips"]


        api = "https://api.census.gov/data/2017/pep/population?get=POP,GEONAME&for=county:"+fips+"&in=state:12&key=d676620b9d664aca95b6857929058e3773d859d2"
        response = requests.get(api).text[37:-2].split(",")
        print(response)
        population = response[0].replace('\"','').replace('[','')

        final_result = {}
        final_result["disaster_type"] = disaster_type
        final_result["disaster_level"] = disaster_level
        final_result["date"] = date
        final_result["temp"] = temp
        final_result["wind_speed"] = wind_speed
        final_result["lat"] = lat
        final_result["lon"] = lon
        final_result["fips"] = fips
        final_result["population"] = population
        final_result["county_name"] = weather["county_name"].strip("\"")
        final_result["zips"] = weather["zips"]
        final_result["state"] = "florida"
        result[fips] = final_result
    return result


    #for city in weather_result

def getWeatherForecast(url):
    api_key = "843aa416b6aa7766b4b1c035e2cc7a88"

    lines = [line.rstrip('\n') for line in open('data/uscitiesv1.4.dat')]
    weather_result = []
    #requests.get(url).json()
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

def main():
    url="https://samples.openweathermap.org/data/2.5/forecast"
    weather_result = getWeatherForecast(url)
    disaster = findDisaster(weather_result)
    print(json.dumps(disaster, indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
