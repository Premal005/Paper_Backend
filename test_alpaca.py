# quick_test.py
import requests

url = "https://paper-api.alpaca.markets/v2/account"
headers = {
    "APCA-API-KEY-ID": "PKOGCVNN8UCFTAN8NNDA",
    "APCA-API-SECRET-KEY": "x5dBXg1d3BfP66NK0EcGt8MipFZtXfcS"
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")