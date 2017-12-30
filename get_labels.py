import api_info
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

userID = <email_address_to_search>
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

print("The standard Google labels are: ")
for a_label in google_labels:
  print(a_label)
print()
print("Searching for additional labels...")

sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
delegated = sa_creds.create_delegated(api_info.google_email)
http_auth = delegated.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http_auth)
results = service.users().labels().list(userId=userID).execute()
labels = results.get('labels', [])
for a_label in labels:
  if a_label['name'] not in google_labels:
    print("  -- label found: " + a_label['name'])
print()
print("search ended")
print()
exit()
