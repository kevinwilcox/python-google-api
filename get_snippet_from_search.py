import api_info
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

userID = '<email_address>'
# <search_phrase> can be anything you would enter in the GMail search box
# for example:   'subject: "a specific subject" AND from: "a_user@a-domain.com"'
# for more examples, see https://support.google.com/mail/answer/7190?hl=en
query = <search_phrase>

sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
delegated = sa_creds.create_delegated(api_info.google_email)
http_auth = delegated.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http_auth)
results = service.users().messages().list(userId=userID, q=query).execute()
messages = results.get('messages', [])
for a_message in messages:
  mid = a_message['id']
  msg_object = service.users().messages().get(userId=userID,id=mid).execute()
  for a_header in msg_object['payload']['headers']:
    if a_header['name'] == "To":
      print("Recipient is: " + a_header['value'])
    elif a_header['name'] == "From":
      print("Sender is: " + a_header['value'])
    elif a_header['name'] == "Subject":
      print("Subject is: " + a_header['value'])
    elif a_header['name'] == "Message-ID":
      print("Message ID is: " + a_header['value'])
  print("Snippet from email: ")
  snippet = msg_object['snippet']
  print(snippet)
  print()
exit()
