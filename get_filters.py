###
# necessary scopes
# this will work with any of the following:
#   https://www.googleapis.com/auth/gmail.readonly
#   https://www.googleapis.com/auth/gmail.modify
#   https://mail.google.com/
#
# I recommend the gmail.readonly scope if not using delete_message or get_snippet_from_search
###

import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

###
# if arguments can't be parsed then there is no use to continue
# --user should support "all" but that means using the Directory API to get all users
#   then iterating through that list, potentially problematic for larger environments
###
try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; this is a required field", default = '')
  args = parser.parse_args()
  user_id = args.user
except Exception as e:
  print("Error: couldn't assign a value to user_id")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

###
# --user is not optional at this point
###
if user_id == '':
  print()
  print("No user was provided.")
  print("Please re-run with --user <>, where the username is the user's complete email address")
  print("Exiting...")
  print()
  exit()

###
# attempt to connect to Google using the oauth2 token and provided email for delegation
# note the reports API doesn't need to act on behalf of any particuler user
###
try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(user_id)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google with the provided information")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  results = service.users().settings().filters().list(userId=user_id).execute()
  filters = results.get('filter', [])
except Exception as e:
  print("Error: connected to Google but couldn't retrieve activities")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  for a_filter in filters:
    crit = a_filter['criteria']
    action = a_filter['action']
    print()
    print("filter found: " + a_filter['id'])
    if 'from' in crit:
      print("  -- filter requires from: " + crit['from'])
    if 'to' in crit:
      print("  -- filter requires to: " + crit['to'])
    if 'subject' in crit:
      print("  -- filter requires subject: " + crit['subject'])
    if 'query' in crit:
      print("  -- filter requires 'includes words': " + crit['query'])
    if 'negatedQuery' in crit:
      print("  -- filter requires 'doesn\'t have': " + crit['negatedQuery'])
    if 'hasAttachment' in crit and crit['hasAttachment'] == True:
      print("  -- filter requires an attachment")
    if 'excludeChats' in crit and crit['excludeChats'] == True:
      print("  -- filter excludes chats/hangouts")
    if 'size' in crit and crit['sizeComparison'] == 'larger':
      print("  -- filter requires size greater than " + crit['size'])
    elif 'size' in crit and crit['sizeComparison'] == 'smaller':
      print("  -- filter requires size smaller than " + crit['size'])

    if 'addLabelIds' in action:
      print("  -- filter adds the following labels: " + action['addLabelIds'])
    if 'removeLabelIds' in action:
      print("  -- filter removes the following labels: " + action['removeLabelIds'])
  print()
  print("no remaining filters")
  print()
except Exception as e:
  print("Error: couldn't iterate through the filter list")
  print(repr(e))
  print()

exit()
