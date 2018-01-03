import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

google_labels = [ "CHAT",
                  "SENT",
                  "SPAM",
                  "DRAFT",
                  "INBOX",
                  "TRASH",
                  "UNREAD",
                  "STARRED",
                  "IMPORTANT",
                  "CATEGORY_SOCIAL",
                  "CATEGORY_FORUMS",
                  "CATEGORY_UPDATES",
                  "CATEGORY_PERSONAL",
                  "CATEGORY_PROMOTIONS" ]

try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; the default is all", default = 'all')
  args = parser.parse_args()
  user_id = args.user
except Exception as e:
  print("Error: couldn't assign a value to user_id")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

print("The standard Google labels are: ")
for a_label in google_labels:
  print(a_label)
print()
print("Searching for additional labels...")

try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(user_id)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  results = service.users().labels().list(userId=user_id).execute()
  labels = results.get('labels', [])
  for a_label in labels:
    if a_label['name'] not in google_labels:
      print("  -- label found: " + a_label['name'])
  print()
  print("search ended")
  print()
except Exception as e:
  print("Error: could connect to Google but couldn't retrieve user's labels")
  print(repr(e))
  print()

exit()
