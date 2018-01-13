###
# The Audit API doesn't correctly log the creation of new Team Drives
# If a new TD is created with no additional immediate activity then a "create" is logged
# If a new TD is created with someone added to it then no "create" is logged
#   -- however, a team_drive_membership_change is logged
# This script is not named "get_new_team_drives" because of that ambiguity
# To detect new TDs, maintain a list of TDs in your SIEM and then for each
#   "create" or "team_drive_membership_change" activity, query if the name
#   and owner exist; if not, add it as a new TD
###

import time
import api_info
import argparse
import httplib2
from apiclient import discovery
from datetime import datetime, timezone
from oauth2client.service_account import ServiceAccountCredentials

###
# Google expects timestamps to be formatted as:
# 2000-01-31T00:00:00Z
# or
# 2000-01-31T00:00:00+00:00
# the time doesn't need to be in UTC but the 'Z' or offset must be present
# this function converts a Unix timestamp (seconds since epoch) into ISO format
# note this isn't used for user-provided times, it is only used if no start or end time is provided
###
def convert_to_ISO(unixTime):
    temp_ts = datetime.fromtimestamp(unixTime, tz = timezone.utc)
    replaced_ts = temp_ts.replace(microsecond=0)
    return replaced_ts.isoformat()

###
# by default, the script will pull all drive logs for the last week
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
  parser.add_argument('--alldrives', help="list all drives in the domain; this only needs to be added, it doesn't need 'true' or 'false'; default is false", action='store_true')
  parser.add_argument('--after', help="only search for Team Drives created after <time>; format must be YYYY-MM-DDTHH:mm:ssTZOFFSET; the default is 'as far back as Google has data'", default = '')
  parser.add_argument('--before', help="only search for Team Drives created before <time>; format must be YYYY-MM-DDTHH:mm:ssTZOFFSET; the default upper bound is now", default = '')
  parser.add_argument('--count', help="the number of results to return per request; the script will request until all Team Drives have been retreived but will do so in 'count'-sized chunks; the default (and max) is 100", default = 100)
  args        = parser.parse_args()
  time_start  = args.after
  time_end    = args.before
  max_results = args.count
  all_drives  = args.alldrives

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
  service = discovery.build('drive', 'v3', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google with the provided information")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

###
# retrieve all drive "team_drive_membership_change" activities, append them to the activities list
###
try:
  c_time = ''
  if time_start != '':
    c_time += "createdTime >= '" + time_start + "'"
    if time_end != '':
      c_time += " AND "
  if time_end != '':
    c_time += "createdTime <= '" + time_end + "'"
  results = service.teamdrives().list(q=c_time, useDomainAdminAccess=all_drives, fields='nextPageToken, teamDrives(id, name, createdTime)').execute()
    #results = service.teamdrives().list(useDomainAdminAccess=all_drives, fields='nextPageToken, teamDrives(id, name, createdTime)').execute()
  if 'teamDrives' in results:
    team_drives = []
    team_drives.extend(results.get('teamDrives', []))
  while 'nextPageToken' in results:
    time.sleep(0.25)
    page_token = results['nextPageToken']
    results = service.teamdrives().list(q=c_time, useDomainAdminAccess=all_drives, fields='nextPageToken, teamDrives(id, name, createdTime)', pageToken=page_token).execute()
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
