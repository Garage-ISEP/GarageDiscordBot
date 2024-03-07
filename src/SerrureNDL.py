import requests
import random
import os
from datetime import datetime, timedelta

SMARTLOCKID = int(os.getenv("SMARTLOCK_ID"))
TOKEN = os.getenv("NUKI_API_TOKEN")
URL = f'https://api.nuki.io/smartlock/{SMARTLOCKID}/auth'
HEADER = {
    'accept': 'application/json',
    'authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
}

def generate_code():
    code = str(random.randint(2,9))
    for k in range(5):
        code += str(random.randint(1,9))
    return code

def AddOTP(name, begin, end):
    valid = False
    while valid == False:
        code = generate_code()

        data = {
            "name": name,
            "allowedFromDate": begin,
            "allowedUntilDate": end,
            "allowedWeekDays": 127,
            "allowedFromTime": 0,
            "allowedUntilTime": 0,
            "accountUserId": 0,
            "remoteAllowed": False,
            "smartActionsEnabled": False,
            "type": 13,
            "code": code
        }

        response = requests.put(URL, headers=HEADER, json=data)

        if (response.status_code == 204):
            valid = True
            return code
        elif ("'code' exists already" in response.text):
            continue
        else:
            print(response.text)
            return "ERROR"

def AddOTP_D(name, dure):
    """
    take a name and a duration, in minutes. And generate an OTP code.
    """
    time = datetime.utcnow()
    begin = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end = (time + timedelta(minutes=dure)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return AddOTP(name, begin, end)


def PurgeOutdatedOTP():
    url = "https://api.nuki.io/smartlock/auth?types=13"
    response = requests.get(url, headers=HEADER)
    status = False
    if response.status_code == 200:
        data = response.json()
        for item in data:
            if 'allowedUntilDate' in item: # Some item are not OTP, so we need to check if the key allowedUntilDate is present
                if datetime.strptime(item['allowedUntilDate'], "%Y-%m-%dT%H:%M:%S.%fZ") < datetime.utcnow():
                    rep = requests.delete("https://api.nuki.io/smartlock/auth", headers=HEADER, json=[item['id']])
                    if rep.status_code == 204:
                        print(f"Deleted {item['name']}")
                        status = True
                    else:
                        print(f"Error deleting {item['name']}")
    else:
        print("Error getting the list of OTPs")
    return status

