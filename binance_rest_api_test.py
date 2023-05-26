import requests

url = 'https://fapi.binance.com/fapi/v1/listenKey'
api_key = 'd4g8tK4spj6opzAlAwJCqS81449pRDqtNEQZE24lB2xYfWvT089GuZS6LfmEGG7U'
secret_key = 'bJLJVdKvAERrtBEJ19SVCdR18kXzuVeyt4fD27lGnkJPbVigrKq8sVCNmlfHLbPB'

headers = {
    'X-MBX-APIKEY': api_key
}

response = requests.post(url, headers=headers, verify=False)

if response.status_code == 200:
    print("User data stream created successfully.")
else:
    print("Failed to create user data stream.")
