#! /usr/bin/env python3
import sys
import os
import requests
import time
import datetime
import json
from dotenv import load_dotenv

load_dotenv()
WEATHER_KEY = os.getenv('WEATHER_KEY')

def fetch_train_data(timestamp_start, timestamp_end, city_name):
  endpoint = f"http://history.openweathermap.org/data/2.5/history/city?q={city_name},FI&type=hour&start={timestamp_start}&end={timestamp_end}&appid={WEATHER_KEY}"

  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run with a {request.status_code}")


def save_data_to_json(file, data):
  if not os.path.isdir("data"):
    os.makedirs("data")

  f = open(f"data/{file}.json", "w")
  f.write(json.dumps(data, indent=2))
  f.close()
  print(f"Weather data fetching successful: {file}")


def read_guide_file_for_fetching():
  # Opening JSON file
  f = open('WeatherDataQueries.json',) 
  # returns JSON object as
  # a dictionary
  weather_data = json.load(f) 
  # Closing file
  f.close()
  return weather_data


if __name__ == "__main__":
  weather_data = read_guide_file_for_fetching()
  start_day = weather_data['start_day']
  end_day = weather_data['end_day']
  timestamp_start = int(time.mktime(datetime.datetime.strptime(start_day, "%Y-%m-%d").timetuple()))
  timestamp_end = int(time.mktime(datetime.datetime.strptime(end_day, "%Y-%m-%d").timetuple()))
  for city in weather_data['city_list']:
    city_name = city['city']
    train_data = fetch_train_data(timestamp_start, timestamp_end, city_name)
    save_data_to_json(f"WeatherData_{city_name}_{start_day}_{end_day}", train_data)
