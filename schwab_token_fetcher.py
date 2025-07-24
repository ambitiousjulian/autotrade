import requests
import base64

appKey = "9fFeTEuASMsx30SbPQRB1UDwGPiFc3Zu"
appSecret = "6tmEJ2GLAOgHyFev"

authUrl = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={appKey}&redirect_uri=https://127.0.0.1"

print(f"Click to authenticate: {authUrl}")

returnedLink = input("Paste the redirect URL here:")

code = f"{returnedLink[returnedLink.index('code=')+5:returnedLink.index('%40')]}@"

headers = {'Authorization': f'Basic {base64.b64encode(bytes(f"{appKey}:{appSecret}", "utf-8")).decode("utf-8")}'}
data = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': 'https://127.0.0.1'}

response = requests.post(url='https://api.schwabapi.com/v1/oauth/token', headers=headers, data=data)
tD = response.json()

access_token = tD['access_token']
refresh_token = tD['refresh_token']

print(f"\nAccess Token: {access_token}")
print(f"\nRefresh Token: {refresh_token}")

# Test it by getting accounts
base_url = "https://api.schwabapi.com/trader/v1/"
response = requests.get(url=f'{base_url}/accounts/accountNumbers', headers={'Authorization': f'Bearer {access_token}'})
print(response.json())