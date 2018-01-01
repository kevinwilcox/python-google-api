import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; the default is all", default = '')
  parser.add_argument('--query', help="the string to search; for examples, see https://support.google.com/mail/answer/7190?hl=en", default = '')
  args = parser.parse_args()
  userID  = args.user
  query   = args.query
except Exception as e:
  print("Error: couldn't assign the provided values")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

if userID == '':
  print()
  print("No user was provided; this script requires a user")
  print("Please run again with --user <email_address>")
  print()
  exit()

try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(api_info.google_email)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1', http=http_auth)
except Exception as e:
  print()
  print("Error: couldn't connect to Google")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

try:
  results = service.users().messages().list(userId=userID, q=query).execute()
  messages = results.get('messages', [])
except Exception as e:
  print()
  print("Error: could connect to Google but couldn't retrieve the list of message IDs")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

try:
  print()
  for a_message in messages:
    mid = a_message['id']
    try:
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
      print(msg_object['snippet'].encode('utf-8', 'ignore'))
      print()
    except Exception as e:
      print("Error: couldn't retrieve the message with ID: " + mid)
      print("This is NOT a fatal error, continuing with next message")
      print()
      pass
except Exception as e:
  print()
  print("Error: couldn't iterate through the message ID list")
  print(repr(e))
  print()

exit()
