import pandas as pd
import numpy as np
import datetime
import time
from dateutil.relativedelta import relativedelta
from sklearn import linear_model, model_selection, pipeline, preprocessing

from fetchTrainData import fetch_train_data
from fetchWeatherData import fetch_weather_data, save_weather_data, open_weather_data
from twitterBot import tweet_station_congested

weather_data = {}

def get_weather(stop_):
    tag = stop_['station.shortCode']
    if type(tag) == str:
        lat = stop_['station.location'][0]
        lon = stop_['station.location'][1]
        if tag not in weather_data:
            print("FETCHING DATA FOR: " + tag, end = "\r")
            weather_data[tag] = fetch_weather_data(unix_time, lat, lon)['list'][0]['main']['temp']

            
def extract_time_tables(train_stops_):
    print("TRAIN NUMBER " + str(train_stops_.name) + ", " + str(float(train_stops_.name) / number_of_trains), end = "\r")
    train_stops = pd.json_normalize(train_stops_)
    to_return = train_stops['differenceInMinutes'].sum()
    train_stops = train_stops.drop(['differenceInMinutes'], axis=1)

    train_stops.apply(get_weather, axis=1)

    for stop in train_stops['station.shortCode'].unique():
        if type(stop) == str:
            if stop not in df.columns:
                df[stop] = np.nan

            df[stop][train_stops_.name] = weather_data[stop]
        
    
    return to_return

tweet = True # Should results be tweeted about, or just printed
loops = 12 # How many months data we want in the dataframe, apparently we can't get over 12 months data
number_of_trains = 750 # How many trains to fetch per month. Seems to be softlocked at about 1000, 500 is safe
all_data_frames = []
all_late_amounts = []


for i in range(loops):
    date = datetime.date.today() - relativedelta(months = i)
    unix_time = time.mktime(date.timetuple())
    print()
    print("LOOP " + str(i) + ", DATE: " + str(date))

    q = (
        """ 
        {
        """
          f'  trainsByDepartureDate(departureDate: \"{date}\",'
        """
        """
          f'  take: {number_of_trains},'
        """
            where: {
                and: [
                    {or: [{deleted: {unequals: null}}, 
                    {deleted: {equals: false}}]}, 
                    {cancelled: {equals: false}}, 
                    {operator: {shortCode: {equals: "vr"}}}
                    ]  
            }
          ) 
          {
            trainNumber
            departureDate
            timeTableRows {
            differenceInMinutes
              station {
                shortCode
                location
              }
            }
          }
        }
        """
        )

    result = fetch_train_data(q)
    recs = result['data']['trainsByDepartureDate']

    df = pd.json_normalize(recs)
    all_stops = pd.json_normalize(df['timeTableRows'])
    df = df.drop(['timeTableRows'], axis=1)

    weather_data = open_weather_data(date)
    how_much_late = all_stops.apply(extract_time_tables, axis=1)
    save_weather_data(date, weather_data)
    
    df['departureDate'] = date.month
    
    all_data_frames.append(df)
    all_late_amounts.append(how_much_late)
    
combined_train_data = pd.concat(all_data_frames).fillna(0).reset_index().drop(['index'], axis=1)
combined_late_amounts = pd.concat(all_late_amounts).fillna(0).reset_index().drop(['index'], axis=1)

combined_late_amounts.rename(columns={0: "total_late"}, inplace=True)
combined_late_amounts = combined_late_amounts["total_late"].apply(lambda x: int(x > 4))

print()
print("DONE MAKING DATAFRAME")

best_score = 0
best_reg = linear_model.SGDClassifier(max_iter=1000)

for i in range(50):
    print(i, end = "\r")
    training_data, test_data, train_target, test_target = model_selection.train_test_split(combined_train_data, combined_late_amounts, train_size=0.8)
    train_target = np.ravel(train_target)
    test_target = np.ravel(test_target)

    reg = linear_model.SGDClassifier(max_iter=1000)
    reg.fit(training_data, train_target)
    reg_score = reg.score(test_data, test_target)
    if reg_score > best_score:
        best_score = reg_score
        best_reg = reg
        print("NEW BEST SCORE: " + str(best_score))
        
print(best_reg.score(test_data, test_target))

def extract_time_tables_station(train_stops_):
    train_stops = pd.json_normalize(train_stops_)

    train_stops.apply(get_weather, axis=1)

    for stop in train_stops['station.shortCode'].unique():
        if type(stop) == str:
            if stop not in df.columns:
                df[stop] = np.nan

            df[stop][train_stops_.name] = weather_data[stop]
            
# List here stations that are checked, and possible tweeted about
stations_to_check = [('HKI', 'Helsinki'), ('PSL', 'Pasila'), ('TKL', 'Tikkurila'), ('KE', 'Kerava'), 
                     ('JNS', 'Joensuu'), ('TPE', 'Tampere'), ('TKU', 'Turku'), ('HL', 'Hämeenlinna'), 
                     ('OL', 'Oulu'), ('SK', 'Seinäjoki'), ('JY', 'Jyväskylä'), ('KV', 'Kouvola')]
results = []


for station in stations_to_check:
    date = datetime.date.today()
    unix_time = time.mktime(date.timetuple())
    
    q = (
        """ 
        {
        """
          f'  trainsByStationAndQuantity(station: "{station[0]}",'
        """
        """
          f'  take: {200},'
        """
            where: {
                and: [
                    {or: [{deleted: {unequals: null}}, 
                    {deleted: {equals: false}}]}, 
                    {cancelled: {equals: false}}, 
                    {operator: {shortCode: {equals: "vr"}}}
                    ]  
            }
          ) 
          {
            trainNumber
            departureDate
            timeTableRows {
              station {
                shortCode
                location
              }
            }
          }
        }
        """
        )
    
    result = fetch_train_data(q)
    recs = result['data']['trainsByStationAndQuantity']

    df = pd.json_normalize(recs)
    all_stops = pd.json_normalize(df['timeTableRows'])
    df = df.drop(['timeTableRows'], axis=1)
    
    weather_data = open_weather_data(date)
    all_stops.apply(extract_time_tables_station, axis=1)
    save_weather_data(date, weather_data)
    
    df['departureDate'] = date.month
    df.fillna(0, inplace=True)
    
    for station in best_reg.feature_names_in_:
        if station not in df.columns:
            df[station] = 0.0
            
    for station in df.columns:
        if station not in best_reg.feature_names_in_:
            df.drop([station], inplace=True, axis=1)
    
    how_many_late = 0
    predictions = best_reg.predict(df)
    for prediction in predictions:
        if prediction == 1:
            how_many_late = how_many_late + 1
            
    results.append(round((how_many_late / len(predictions)) * best_score, 2))  # What percent of trains does the algorithm think are going to be late
    
if tweet:
    for i, val in enumerate(stations_to_check):
        if results[i] > 0.65:
            tweet_station_congested(val[1], results[i])
            print(f"TWEETED ABOUT {val[1]} BEING CONGESTED")
else:
    print(stations_to_check)
    print(results)

print("DONE!!")