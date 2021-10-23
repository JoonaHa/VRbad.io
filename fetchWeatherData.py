#! /usr/bin/env python3
import sys
import os
from os.path import exists
import requests
import math
import time
import calendar
from datetime import datetime, date, timedelta, timezone
import json
from dotenv import load_dotenv

load_dotenv()
WEATHER_KEY = os.getenv('WEATHER_KEY')


def get_stations():
  endpoint = f"https://rata.digitraffic.fi/api/v1/metadata/stations"
  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run to get stations")


def get_station_info(station_short_code):
  for station in get_stations():
    if station["stationShortCode"] == station_short_code:
      return station
  return {}
    

def fetch_weather_data(start, end, lon, lat):
  endpoint = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={WEATHER_KEY}"
  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run with a {request.status_code}")


def save_weather_between_dates(date_start, date_end, station_short_code):
  date_start_datetime = datetime(date_start.year, date_start.month, date_start.day, 0, 0, 0, 0, tzinfo=timezone.utc)
  date_end_datetime = datetime(date_end.year, date_end.month, date_end.day, 0, 0, 0, 0, tzinfo=timezone.utc)
  timestamp_start = calendar.timegm(date_start_datetime.utctimetuple())
  timestamp_end = calendar.timegm(date_end_datetime.utctimetuple())

  if exists(f"data/Weather_{station_short_code}.json") == False:
    station = get_station_info(station_short_code)
    longitude = station["longitude"]
    latitude = station["latitude"]
    all_weeks = []
    for week_count in range(0, int(math.ceil((date_end - date_start).days / 7))):
      timestamp_start_week = timestamp_start + week_count * 60 * 60 * 24 * 7
      new_data = fetch_weather_data(timestamp_start_week, timestamp_end, longitude, latitude)
      all_weeks.append(new_data)
    save_data_to_json(f"Weather_{station_short_code}", all_weeks)
  return


def save_data_to_json(file, data):
  if not os.path.isdir("data"):
    os.makedirs("data")

  f = open(f"data/{file}.json", "w")
  f.write(json.dumps(data, indent=2))
  f.close()


def open_data_from_json(file):
  f = open(f"data/{file}.json",)
  data = json.load(f)
  f.close()
  return data


def collect_weather_data_for_station(station_short_code, date_start, date_end):
  save_weather_between_dates(date_start, date_end, station_short_code)
  list_of_weather = {}
  if exists(f"data/Weather_{station_short_code}.json"):
    data = open_data_from_json(f"Weather_{station_short_code}")
    for week in data:
      for datapoint in week["list"]:
        list_of_weather[datapoint["dt"]] = datapoint
  return list_of_weather


if __name__ == "__main__":
  date_start = date(2020, 10, 25)
  date_end = date(2021, 10, 21)
  station_short_code = "MI"
  weather = collect_weather_data_for_station(station_short_code, date_start, date_end)
  print(weather)
