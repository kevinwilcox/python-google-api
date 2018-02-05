###
# The Audit API doesn't correctly log the creation of new Team Drives
# Instead, this uses the "Drive" API to look for TDs created inside
#   of a given time window
# The default time window begins with the first TD created and ends with now
#
# This script needs ONE of the following scopes:
# https://www.googleapis.com/auth/drive
# https://www.googleapis.com/auth/drive.readonly
###

import time
import api_info
import argparse
import httplib2
from apiclient import discovery
from datetime import datetime, timezone
from oauth2client.service_account import ServiceAccountCredentials

###
# if arguments can't be parsed then there is no use to continue
###
try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--after', help="only search for Team Drives created after <time>; format must be YYYY-MM-DDTHH:mm:ssTZOFFSET; the default is 'as far back as Google has data'", default = '')
  parser.add_argument('--before', help="only search for Team Drives created before <time>; format must be YYYY-MM-DDTHH:mm:ssTZOFFSET; the default upper bound is now", default = '')
  parser.add_argument('--count', help="the number of results to return per request; the script will request until all Team Drives have been retreived but will do so in 'count'-sized chunks; the default (and max) is 100", default = 100)
  args        = parser.parse_args()
  time_start  = args.after
  time_end    = args.before
  max_results = args.count

except Exception as e:
  print("Error: couldn't assign a value to user_id")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

###
# attempt to connect to Google using the oauth2 token and provided email for delegation
# note the reports API doesn't need to act on behalf of any particuler user but
#   does need to be a superadmin account (or account with full Drive permissions
#   in the Google Admin configuration)
###
try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(api_info.google_email)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('drive', 'v3', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google with the provided information")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

###
# retrieve all Team Drives within the time window
###
try:
  c_time = ''
  if time_start != '':
    c_time += "createdTime >= '" + time_start + "'"
    if time_end != '':
      c_time += " AND "
  if time_end != '':
    c_time += "createdTime <= '" + time_end + "'"
  results = service.teamdrives().list(q=c_time, useDomainAdminAccess=True, fields='nextPageToken, teamDrives(id, name, createdTime)', pageSize=max_results).execute()
  if 'teamDrives' in results:
    team_drives = []
    team_drives.extend(results.get('teamDrives', []))
  while 'nextPageToken' in results:
    time.sleep(0.25)
    page_token = results['nextPageToken']
    results = service.teamdrives().list(q=c_time, useDomainAdminAccess=True, fields='nextPageToken, teamDrives(id, name, createdTime)', pageToken=page_token, pageSize=max_results).execute()
    team_drives.extend(results.get('teamDrives', []))
except Exception as e:
  print("Error: connected to Google but couldn't retrieve team drives")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  for a_drive in team_drives:
    print(a_drive)
except Exception as e:
  print("Error: connected to Google but couldn't retrieve 'add_to_team_drive' activities")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

print()
exit()
