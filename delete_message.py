import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

# a note on scopes
# moving items to the Bin can be accomplished with:
#   https://www.googleapis.com/auth/gmail.modify
# this scope does NOT allow you to do a permanent delete
# in order to skip the Bin and delete the message permanently, you need:
#   https://mail.google.com
# I do not recommend this unless you are 100% sure you need to do this
try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; this must be an email address or 'any', there is no default", default = '')
  parser.add_argument('--query', help="the string to search; for examples, see https://support.google.com/mail/answer/7190?hl=en", default = '')
  parser.add_argument('--skip-bin', help="the default action is to move to Bin; specify this flag to skip the Bin", dest='skip_bin', action='store_true')
  args      = parser.parse_args()
  userID    = args.user
  query     = args.query
  skip_bin  = args.skip_bin
except Exception as e:
  print("Error: couldn't assign the provided values")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

if query == '':
  print()
  print("No query string was provided. This will delete everything in the user's mailbox.")
  print("This is highly destructive; to perform this action use GAM or remove this safety check")
  print("Please re-run with --query <>, where the query string follows https://support.google.com/mail/answer/7190?hl=en")
  print("Exiting...")
  print()
  exit()

if userID == '':
  print()
  print("No user was provided; this script requires a user")
  print("Please run again with --user <email_address> or --user any")
  print()
  exit()

try:
  sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
  delegated = sa_creds.create_delegated(api_info.google_email)
  http_auth = delegated.authorize(httplib2.Http())
  service = discovery.build('admin', 'directory_v1', http=http_auth)
except Exception as e:
  print("Error: couldn't connect to Google with the provided information")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

if userID == 'any':
  try:
    results = service.users().list(domain=api_info.google_domain, orderBy='email').execute()
    domain_users = results.get('users', [])
  except Exception as e:
    print("Error: couldn't retrieve user list")
    print(repr(e))
    print("This is a fatal error, exiting")
    exit()
  user_id_list = []
  for a_domain_user in domain_users:
    user_id_list.append(a_domain_user['primaryEmail'])
else:
  user_id_list = [userID]

for current_user_id in user_id_list:
  print()
  print("searching mail for: " + current_user_id)
  try:
    sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
    delegated = sa_creds.create_delegated(current_user_id)
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
    results = service.users().messages().list(userId=current_user_id, q=query).execute()
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
    interesting_headers = [ "To", "From", "Subject", "Message-ID", "Cc", "Bcc"]
    acceptable_verify_resp = ['y', 'n']
    for a_message in messages:
      mid = a_message['id']
      verify = ''
      try:
        msg_object = service.users().messages().get(userId=current_user_id,id=mid).execute()
        for a_header in msg_object['payload']['headers']:
          if a_header['name'] in interesting_headers:
            print(a_header['name'] + " is: " + a_header['value'])
        print()
        while verify not in acceptable_verify_resp:
          verify = input("Do you want to delete this message, 'y' or 'n'? ").lower()
        if verify == 'y':
          print()
          print("You chose yes, message will be deleted")
          try:
            if skip_bin == True:
              deleted = service.users().messages().delete(userId=current_user_id, id=mid).execute()
            else:
              deleted = service.users().messages().trash(userId=current_user_id, id=mid).execute()
            print("Delete request sent, continuing")
            print()
          except Exception as e:
            print("Error deleting this message")
            print("Error message: " + repr(e))
            print("This is not a fatal error, continuing")
        else:
          print()
          print("You chose no, skipping this message")
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
  print("No additional messages match for " + current_user_id)
  print("Continuing to next user")
  print()
print("All users searched, exiting")
exit()
