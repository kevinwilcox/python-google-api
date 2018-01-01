import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; the default is all", default = 'all')
  args = parser.parse_args()
  userID = args.user
except Exception as e:
  print("Error: couldn't assign a value to userID")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(api_info.google_email)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('admin', 'reports_v1', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google with the provided information")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  results = service.activities().list(userKey=userID, applicationName='login').execute()
  activities = results.get('items', [])
except Exception as e:
  print("Error: connected to Google but couldn't retrieve activities")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  for activity in activities:
    print()
    print("New login record")
    print("Time: " + activity['id']['time'])
    print("Email Address: " + activity['actor']['email'])
    print("IP Address: " + activity['ipAddress'])
    print("Event result: " + activity['events'][0]['name'])
except Exception as e:
  print("Error: couldn't iterate through the activity list")
  print(repr(e))
exit()
