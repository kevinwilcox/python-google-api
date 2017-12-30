import api_info
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
delegated = sa_creds.create_delegated(api_info.google_email)
http_auth = delegated.authorize(httplib2.Http())
service = discovery.build('admin', 'reports_v1', http=http_auth)
results = service.activities().list(userKey='all', applicationName='login').execute()
activities = results.get('items', [])
for activity in activities:
  print()
  print("New login record")
  print("Time: " + activity['id']['time'])
  print("Email Address: " + activity['actor']['email'])
  print("IP Address: " + activity['ipAddress'])
  print("Event result: " + activity['events'][0]['name'])
exit()
