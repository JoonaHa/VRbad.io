#! /usr/bin/env python3
import sys
import os
from os.path import exists
import requests
import json
import numpy as np
import pandas as pd
import time
import datetime
import calendar
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv
from sklearn import linear_model
import statsmodels.api as sm


def get_stations():
  endpoint = f"https://rata.digitraffic.fi/api/v1/metadata/stations"
  print(f"Endpoint: {endpoint}")

  request = requests.get(endpoint)
  if request.status_code == 200:
      return request.json()
  else:
      raise Exception(f"Query failed to run to get stations")


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


def calculate_difference_to_mean(row, grouped_df):
  #print(type(to_total_seconds(row['Arrival'])))
  #print(type(row['unix_time']))
  return row['unix_time'] - grouped_df.get(row['Station']).get(row['TrainNro'])

def get_weekday(day):
  day_number = day.date().weekday()
  options = {0 : "Sunday",
             1 : "Monday",
             2 : "Tuesday",
             3 : "Wednesday",
             4 : "Thursday",
             5 : "Friday",
             6 : "Saturday",
  }
  return options[day_number]


def set_weekdayvalue(row, weekday):
  if row['Week_day'] == weekday:
    return 1
  else:
    return 0


def collect_weather_data():
  weathers = {}
  for station in get_stations():
    if station["passengerTraffic"] == True:
      station_short_code = station["stationShortCode"]
      list_of_weathers = {}
      if exists(f"data/Weather_{station_short_code}.json"):
        data = open_data_from_json(f"Weather_{station_short_code}")
        for week in data:
          for datapoint in week["list"]:
            list_of_weathers[datapoint["dt"]] = datapoint
      weathers[station_short_code] = list_of_weathers
  return weathers


def collect_weather_data_for_station(station_short_code):
  list_of_weather = {}
  if exists(f"data/Weather_{station_short_code}.json"):
    data = open_data_from_json(f"Weather_{station_short_code}")
    for week in data:
      for datapoint in week["list"]:
        list_of_weather[datapoint["dt"]] = datapoint
  return list_of_weather


def round_timestamp_to_upper_hour(timestamp):
  hours = int(timestamp / 3600)
  return hours * 3600

def get_temperature(row, weather_for_station):
  timestamp = round_timestamp_to_upper_hour(time.mktime(row['Arrival'].timetuple()))
  if timestamp in weather_for_station:
    temp = weather_for_station[timestamp]["main"]["temp"] - 273.15
    return temp
  return "NA"
  

def collect_df(station_short_code):
  df = pd.read_csv(f"data/Trains_{station_short_code}.json")

  df['DepartureDate'] = pd.to_datetime(df['DepartureDate'])
  df['DepartureDate_FI'] = df['DepartureDate'].dt.tz_localize('Europe/Helsinki')

  df['Arrival'] = pd.to_datetime(df['Arrival'], utc=True)
  df['Arrival_FI'] = df['Arrival'].dt.tz_convert('Europe/Helsinki')

  df['Week_day'] = df.apply (lambda row: get_weekday(row['DepartureDate_FI']), axis=1)
  df['unix_time'] = (df['Arrival_FI'] - df['DepartureDate_FI']).dt.total_seconds()

  weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  for weekday in weekdays:
      df[weekday] = df.apply (lambda row: set_weekdayvalue(row, weekday), axis=1)

  grouped_df = df.groupby(['Station', 'TrainNro'])['unix_time'].mean()
  df['Diff_against_mean'] = df.apply (lambda row: calculate_difference_to_mean(row, grouped_df), axis=1)

  weather_for_station = collect_weather_data_for_station(station_short_code)
  df['Temperature'] = df.apply (lambda row: get_temperature(row, weather_for_station), axis=1)

  df = df.drop(df[df['Temperature'] == 'NA'].index)

  print(df.iloc[0])

  return df


def linear_regression(station_data):
  selected_columns = ['Temperature', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  X = station_data[selected_columns]
  Y = station_data['Diff_against_mean']

  # with sklearn
  regr = linear_model.LinearRegression()
  regr.fit(X, Y)

  print('Intercept: \n', regr.intercept_)
  print('Coefficients: \n', regr.coef_)

  # with statsmodels
  X = sm.add_constant(X) # adding a constant
 
  model = sm.OLS(Y, X.astype(float)).fit()
  predictions = model.predict(X)
 
  print_model = model.summary()
  print(print_model)    

station_data = collect_df("MI")

linear_regression(station_data)


#weather = collect_weather_data_for_station("MI")
#print(weather[1632268800]["main"]["temp"])