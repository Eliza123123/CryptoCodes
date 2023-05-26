import json
import requests
import time

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
    'start': '1',
    'convert': 'USD',
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '01838615-14d0-4655-8c4c-5d59e2d4cdbe',
}
filename = 'stored-data.json'


def store_data():
    try:
        response = requests.get(url, params=parameters, headers=headers, verify=False)
        data = json.loads(response.text)

        with open(filename, "w") as stored_data:
            json.dump(data, stored_data, indent=4)
            print("Data stored successfully.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")


# Run the initial store_data call
store_data()


while True:
    # Wait for 5 minutes
    time.sleep(300)
    # Call store_data every 5 minutes
    store_data()
