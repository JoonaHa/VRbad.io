#! /usr/bin/env python3
import os
from os.path import exists
import requests
import json
from dotenv import load_dotenv

load_dotenv()
WEATHER_KEY = os.getenv('WEATHER_KEY')


def fetch_weather_data(time_stamp, lon, lat):
  endpoint = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={time_stamp}&cnt=1&appid={WEATHER_KEY}"
  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      print(request.text)
      raise Exception(f"Query failed to run with a {request.status_code}")


def save_weather_data(file, data):
  if not os.path.isdir("weather_data"):
    os.makedirs("weather_data")

  f = open(f"weather_data/{file}.json", "w")
  f.write(json.dumps(data, indent=2))
  f.close()


def open_weather_data(date):
  data = {}
  if exists(f"weather_data/{date}.json"):
    f = open(f"weather_data/{date}.json",)
    data = json.load(f)
    f.close()
  
  return data

if __name__ == "__main__":
  print(fetch_weather_data(1635195600.0, 22.96829, 59.826866))