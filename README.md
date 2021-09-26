# VRbad.io
Course projects for predicting if VR is bad using statistical methods

# Setting up
Make sure you are in the directory containing this README, and create a python virtual environment with command "python3 -m venv venv". Activate this virtual environment with "source venv/bin/activate". Load the required python packages with "pip install -r requirements.txt"

# Fetching data
Data can be fetched by running the python script fetchTrainData.py. The command requires output file name, and a GraphQL search query. These can be entered before command runs via terminal command "python fetchTrainData.py 'file_name' 'search_query'". The search query will be multiline, so make sure to wrap it with ''. Alternatively the command "python fetchTrainData.py" prompts the user for the output file name and the search query. After inserting the query via copy/paste, use ctrl+d to insert the data.

The fetched data is saved into data -directory with the given name. All data saved is in .json format.

Ready made queries can be found in queries.txt.