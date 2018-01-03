### necessary scopes
# all functionality can be achieved with
#   https://www.googleapis.com/auth/admin.reports.audit.readonly
#

import time
import api_info
import argparse
import httplib2
from apiclient import discovery
from datetime import datetime, timezone
from oauth2client.service_account import ServiceAccountCredentials

def convert_to_ISO(unixTime):
    temp_ts = datetime.fromtimestamp(unixTime, tz = timezone.utc)
    replaced_ts = temp_ts.replace(microsecond=0)
    return replaced_ts.isoformat()

start_timestamp_unix = time.time() - (60 * 60 * 24 * 7)
start_timestamp_iso = convert_to_ISO(start_timestamp_unix)
end_timestamp_unix = time.time()
end_timestamp_iso = convert_to_ISO(end_timestamp_unix)

try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; the default is all", default = 'all')
  parser.add_argument('--start', help="a starting time for the search; format must be YYYY-MM-DDTHH:mm:ssTZOFFSET; the default start is one week ago", default = start_timestamp_iso)
  parser.add_argument('--end', help="an end time for the search; format must be YYYY-MM-DDTHH:mm:ssTZOFFSET; the default end is now", default = end_timestamp_iso)
  parser.add_argument('--count', help="the number of results to return per request; the script will request until all authentication actions have been retreived but will do so in 'count'-sized chunks; the default is 1000", default = 1000)
  args        = parser.parse_args()
  user_id      = args.user
  time_start  = args.start
  time_end    = args.end
  max_results = args.count

except Exception as e:
  print("Error: couldn't assign a value to user_id")
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
  activities = []
  results = service.activities().list(userKey=user_id, applicationName='login', startTime = time_start, endTime = time_end, maxResults = max_results).execute()
  if 'items' in results:
    activities.extend(results.get('items', []))
  while 'nextPageToken' in results:
    time.sleep(0.25)
    page_token = results['nextPageToken']
    results = service.activities().list(userKey=user_id, applicationName='login', startTime = time_start, endTime = time_end, maxResults = max_results, pageToken=page_token).execute()
    activities.extend(results.get('items', []))
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
