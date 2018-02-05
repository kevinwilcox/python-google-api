###
# In incident response it is critical to identify the scope of a compromise
# This script attempts to give context to responders by retrieving all Team Drive
#   permissions based on any of the following criteria:
#   o all Team Drives to which someone has access
#   o all Team Drives whose name includes a given string
#   o all Team Drives for the domain (last resort, this could be a mountain of data)
#
# The first iteration is Team Drives only
# The second iteration will be to return all Drive items that are
#   owned by or shared with a given user
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

try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="if specified, retrieve the permissions for TDs for which this user is a member (organiser, editor, viewer); default is google_email from api_info.py", default = api_info.google_email)
  parser.add_argument('--deleted', help="if specified, show only deleted objects; the default is to not show deleted objects", action='store_true')
  parser.add_argument('--count', help="the number of results to return per request; the script will request until all Team Drives have been retreived but will do so in 'count'-sized chunks; the default (and max) is 100", default = 100)
  args          = parser.parse_args()
  email_address = args.user
  deleted       = args.deleted
  max_results   = args.count

except Exception as e:
  print("Error: couldn't assign a value to user_id")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

if email_address == '':
  print()
  print("A user is required for this script. Please run again with --user <email_address>")
  print("This is a fatal error, exiting...")
  print()
  exit()

try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(email_address)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('drive', 'v2', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google with the provided information")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  td_delegated = sa_creds.create_delegated(api_info.google_email)
  td_http_auth = td_delegated.authorize(httplib2.Http())
  td_service = discovery.build('drive', 'v3', http=td_http_auth)
except Exception as e:
  print("Error: couldn't create delegated token to search team drives")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  perms = service.permissions().getIdForEmail(email=email_address).execute()
  permission_id = perms.get('id')
except Exception as e:
  print("Error: couldn't get permissions ID for " + email_address)
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  service = discovery.build('drive', 'v3', http=http_auth)
  search_query = "trashed = " + str(bool(deleted))
  files = service.files().list(corpora='user', includeTeamDriveItems=True, supportsTeamDrives=True, q=search_query).execute()
except Exception as e:
  print("Couldn't get list of files and team drives to which the user has access")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  previous_td_id = ''
  td_name = ''
  td_role = ''
  for a_file in files['files']:
    print()
    print("item name: " + a_file['name'])
    print("item id: " + a_file['id'])
    if 'teamDriveId' in a_file:
      current_td_id = a_file['teamDriveId']
      if previous_td_id != current_td_id:
        try:
          td_results = td_service.teamdrives().get(teamDriveId=current_td_id, useDomainAdminAccess=True).execute()
          td_name = td_results['name']
        except Exception as e:
          print("Error: couldn't get the name of the team drive with ID " + current_td_id)
          print(repr(e))
          print("This is a fatal error, exiting")
          exit()
        try:
          permissions_results = td_service.permissions().get(fileId=current_td_id, permissionId=permission_id, supportsTeamDrives=True, useDomainAdminAccess=True).execute()
          td_role = permissions_results['role']
        except Exception as e:
          print("Error: couldn't retrieve permissions for team drive with ID " + a_file['teamDriveId'])
          print(repr(e))
          print("This is a fatal error, exiting")
          exit()
      else:
        pass
      previous_td_id = current_td_id
      print("team drive name: " + td_name )
      print("team drive id: " + current_td_id)
      print("minimum role inherited from team drive: " + td_role)
    else:
      results = service.permissions().get(fileId=a_file['id'], permissionId=permission_id).execute()
      print("role: " + results['role'])
except Exception as e:
  print("Error: couldn't iterate list of files/team drives for " + email_address)
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

print()
exit()
