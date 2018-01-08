###
# necessary scopes
# all functionality can be achieved with
#   https://www.googleapis.com/auth/admin.reports.audit.readonly
####

import time
import api_info
import argparse
import httplib2
from apiclient import discovery
from datetime import datetime, timezone
from oauth2client.service_account import ServiceAccountCredentials

###
# Google expects timestamps to be formatted as either:
#
# 2000-01-31T00:00:00Z
#
# or
#
# 2000-01-31T00:00:00+00:00
#
# the time doesn't need to be in UTC but the 'Z' or offset must be present
# this function converts a Unix timestamp (seconds since epoch) into ISO format
# note this isn't used for user-provided times, it is only used if no start or end time is provided
###
def convert_to_ISO(unixTime):
    temp_ts = datetime.fromtimestamp(unixTime, tz = timezone.utc)
    replaced_ts = temp_ts.replace(microsecond=0)
    return replaced_ts.isoformat()

###
# by default, the script will pull all auth logs for the last week
# this sets the timestamps for (now) and (now - 1 week)
###
ts_now = time.time()
start_timestamp_unix = ts_now - (60 * 60 * 24 * 7)
start_timestamp_iso = convert_to_ISO(start_timestamp_unix)
end_timestamp_unix = ts_now
end_timestamp_iso = convert_to_ISO(end_timestamp_unix)

###
# if arguments can't be parsed then there is no use to continue
###
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

###
# attempt to connect to Google using the oauth2 token and provided email for delegation
# note the reports API doesn't need to act on behalf of any particuler user
###
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

###
# retrieve all login activities, store them in an activities list
# do all of the Google requests up-front, all the activity parsing after
# this makes use of the nextPageToken value for paginated results
# the sleep() should be sufficient to prevent rate-limiting from Google
#   -- to-do: implement proper back-off scheduling
###
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

###
# each "login" activity will have:
#    time
#    email address
#    IP Address
#    whether it's a login_success, login_failure or logout event
###
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
