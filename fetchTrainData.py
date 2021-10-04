#! /usr/bin/env python3
import sys
import os
import requests
import json


def get_user_inputs():
  out_file = ""
  query = ""
  if len(sys.argv) == 3:
    out_file = sys.argv[1]
    query = sys.argv[2]
  else:
    out_file = input("Please insert output file name: ")
    print("Please insert GraphQL query (examples here: https://www.digitraffic.fi/rautatieliikenne/#graphql)\n"
    + "Finish giving input with ctrl+d")
    query = "".join(sys.stdin.readlines())
    print("")

  if out_file != "" and query != "":
    return (out_file, query)
  else:
    raise Exception("Given arguments need to be non-empty")


def fetch_train_data(query):
  endpoint = "https://rata.digitraffic.fi/api/v2/graphql/graphql"
  headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip"}

  request = requests.post(endpoint, json={"query": query}, headers=headers)
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
  print("Data fetching successful!")


if __name__ == "__main__":
  user_input = get_user_inputs()
  train_data = fetch_train_data(user_input[1])
  save_data_to_json(user_input[0], train_data)
