#! /usr/bin/env python3
import sys
import os
from os.path import exists
import requests
import math
import json
import pandas as pd
import time
import datetime
import calendar
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
WEATHER_KEY = os.getenv('WEATHER_KEY')


def get_stations():
  endpoint = f"https://rata.digitraffic.fi/api/v1/metadata/stations"
  print(f"Endpoint: {endpoint}")

  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run to get stations")


def fetch_weather_data(start, end, lat, lon):
  print("start_day:", start)
  endpoint = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={WEATHER_KEY}"

  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run with a {request.status_code}")


def save_station_weather_between_dates(date_start, date_end, selected_stations):
  date_start_datetime = datetime(date_start.year, date_start.month, date_start.day, 0, 0, 0, 0, tzinfo=timezone.utc)
  date_end_datetime = datetime(date_end.year, date_end.month, date_end.day, 0, 0, 0, 0, tzinfo=timezone.utc)
  timestamp_start = calendar.timegm(date_start_datetime.utctimetuple())
  timestamp_end = calendar.timegm(date_end_datetime.utctimetuple())

  for station in get_stations():
    if station["passengerTraffic"] == True:
      station_short_code = station["stationShortCode"]
      if len(selected_stations) == 0 or station_short_code in selected_stations:
        print(station_short_code)
        if exists(f"data/Weather_{station_short_code}.json") == False:
          latitude = station["latitude"]
          longitude = station["longitude"]
          all_weeks = []
          for week_count in range(0, int(math.ceil((date_end - date_start).days / 7))):
            timestamp_start_week = timestamp_start + week_count * 60 * 60 * 24 * 7
            new_data = fetch_weather_data(timestamp_start_week, timestamp_end, latitude, longitude)
            all_weeks.append(new_data)
          save_data_to_json(f"Weather_{station_short_code}", all_weeks)
  return


def fetch_train_data_for_day_and_train_number(date, number):
  endpoint = f"https://rata.digitraffic.fi/api/v1/trains/{date}/{number}"
  print(f"Endpoint: {endpoint}")

  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run with a {request.status_code}, date: {date} number: {number}")


def fetch_train_data_for_date(date):
  endpoint = f"https://rata.digitraffic.fi/api/v1/trains/{date}"
  print(f"Endpoint: {endpoint}")

  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run with a {request.status_code}, date: {date} number: {number}")


def datelist_between_dates(sdate, edate):
  delta = edate - sdate
  daylist = []
  for i in range(delta.days + 1):
    day = sdate + timedelta(days=i)
    daylist.append(day)
  return daylist


def add_data(data, date, alldata):
  for train in data:
    train_number = train["trainNumber"]
    train_date = datetime.strptime((train["departureDate"])[:10], '%Y-%m-%d')
    train_date_FI = datetime(train_date.year, train_date.month, train_date.day, 0, 0, 0, 0)
    operator_short_code = train["operatorShortCode"]
    for train_row in train["timeTableRows"]:
      if "type" in train_row and train_row["type"] == "ARRIVAL":
        if "actualTime" in train_row:
          station = train_row["stationShortCode"]
          actual_time = train_row["actualTime"]
          act_dt = datetime.strptime(actual_time[:19], '%Y-%m-%dT%H:%M:%S')
          actual_dt_utc = datetime(act_dt.year, act_dt.month, act_dt.day, act_dt.hour, act_dt.minute, act_dt.second, 0, tzinfo=timezone.utc)
          data_to_add = [station, train_date_FI, train_number, operator_short_code, actual_dt_utc]
          if (station in alldata) == False:
            alldata[station] = []
          alldata[station].append(data_to_add)
  return alldata


def save_train_data_with_date_between(dateStart, dateEnd):
  datelist_between_dates_result = datelist_between_dates(dateStart, dateEnd)
  alldata = {}
  for date in datelist_between_dates_result:
    if exists(f"data/{date}.json"):
      data = open_data_from_json(date)
      print(f"data/{date}.json")
    else:
      data = fetch_train_data_for_date(date)
      save_data_to_json(f"{date}", data)
      print(f"data/{date}.json")
    alldata = add_data(data, date, alldata)
  for station_code, values_to_station in alldata.items():
    if exists(f"data/Trains_{station_code}.json") == False:
      df = pd.DataFrame(values_to_station, columns = ['Station', 'DepartureDate', 'TrainNro', 'Operator', 'Arrival'])
      df.to_csv(f"data/Trains_{station_code}.json") #, index=False, header=False)
  return alldata


def save_data_to_json(file, data):
  if not os.path.isdir("data"):
    os.makedirs("data")

  f = open(f"data/{file}.json", "w")
  f.write(json.dumps(data, indent=2))
  f.close()
  print("Data fetching successful!")


def open_data_from_json(file):
  f = open(f"data/{file}.json",)
  data = json.load(f)
  f.close()
  return data


def fetch_all_data():
  date_start = date(2020, 10, 24)
  date_end = date(2021, 10, 21)

  selected_stations = []

  save_station_weather_between_dates(date_start, date_end, selected_stations)
  save_train_data_with_date_between(date_start, date_end)

date_start = date(2020, 10, 27)
date_end = date(2020, 11, 14)

selected_stations = ['MI', 'HKI', 'KUO']

save_station_weather_between_dates(date_start, date_end, selected_stations)
save_train_data_with_date_between(date_start, date_end)


#fetch_all_data()