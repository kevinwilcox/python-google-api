###
# necessary scopes
# moving items to the Bin can be accomplished with:
#   https://www.googleapis.com/auth/gmail.modify
# this scope does NOT allow you to do a permanent delete
# in order to skip the Bin and delete the message permanently, you need:
#   https://mail.google.com
# I do not recommend this unless you are 100% sure you need to do this
###

import time
import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

###
# error and exit if the command-line arguments can't be assigned
# the default action is to Bin messages (so users can retrieve them if necessary)
# --skip-bin will perform the equivalent of the user deleting from the folder *then deleting from Trash*
###
try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; this must be an email address or 'any', there is no default", default = '')
  parser.add_argument('--query', help="the string to search; for examples, see https://support.google.com/mail/answer/7190?hl=en", default = '')
  parser.add_argument('--skip-bin', help="the default action is to move to Bin; specify this flag to skip the Bin", dest='skip_bin', action='store_true')
  parser.add_argument('--no-confirm', help="WARNING DANGER WARNING this option skips prompting for delete confirmation", dest='no_confirm', action='store_true')
  args          = parser.parse_args()
  user_id       = args.user
  query         = args.query
  skip_bin      = args.skip_bin
  skip_confirm  = args.no_confirm
except Exception as e:
  print("Error: couldn't assign the provided values")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

###
# any delete should require a search string
# failing to provide a string would prompt for every email to be deleted
# deleting all email can be addressed in a different script
###
if query == '':
  print()
  print("No query string was provided. This will delete everything in the user's mailbox.")
  print("This is highly destructive; to perform this action use GAM or remove this safety check")
  print("Please re-run with --query <>, where the query string follows https://support.google.com/mail/answer/7190?hl=en")
  print("Exiting...")
  print()
  exit()

###
# any delete should require a userid
# this should be a single email address or a keyword of 'any'
# 'any' will cause the script to pull an entire user list using the directory API
###
if user_id == '':
  print()
  print("No user was provided; this script requires a user")
  print("Please run again with --user <email_address> or --user any")
  print()
  exit()

###
# retrieve the oauth2 creds and create the SACreds object
# this doesn't change throughout the script so only do it once
###
sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)

###
# connect to Google with the existing SACreds object
# the Directory API can use the address from the config file
# walk the Directory API to get all email addresses associted with the domain
# store those addresses in the domain_users list
###
if user_id == 'any':
  try:
    user_id_list = []
    delegated = sa_creds.create_delegated(api_info.google_email)
    http_auth = delegated.authorize(httplib2.Http())
    service = discovery.build('admin', 'directory_v1', http=http_auth)
    results = service.users().list(domain=api_info.google_domain, orderBy='email').execute()
    ###
    # walk the directory and store the users
    # this is less efficient for small numbers of users but more efficient for thousands of users
    # nextPageToken is a string returned by Google that lets them paginate results
    # nextPageToken will not exist on the last page of results
    ###
    if 'users' in results:
      for a_user in results.get('users', []):
        user_id_list.append(a_user['primaryEmail'])
    while 'nextPageToken' in results:
      time.sleep(0.25)
      page_token = results['nextPageToken']
      results = service.users().list(domain=api_info.google_domain, orderBy='email', pageToken=page_token).execute()
      for a_user in results.get('users', []):
        user_id_list.append(a_user['primaryEmail'])
  except Exception as e:
    print("Error connecting to Google and retrieving user list")
    print(repr(e))
    print("This is a fatal error, exiting")
    exit()

###
# no need to walk the API since a user ID is provided
# add it to the user_id_list list so there's normalisation in later code
###
else:
  user_id_list = [user_id]

for current_user_id in user_id_list:
  print()
  print("searching mail for: " + current_user_id)
  ###
  # a message is associated with an email address
  # that email address must be the one to delegate access to the token
  ###
  try:
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

  ###
  # for each user, get all messages that match the query string
  # this stores all matching messages in a
  ##
  try:
    messages = []
    results = service.users().messages().list(userId=current_user_id, q=query).execute()
    if 'messages' in results:
      messages.extend(results.get('messages', []))
    while 'nextPageToken' in results:
      time.sleep(0.25)
      page_token = results['nextPageToken']
      results = service.users().messages().list(userId=current_user_id, q=query, pageToken=page_token).execute()
      messages.extend(results.get('messages', []))
  except Exception as e:
    print()
    print("Error: could connect to Google but couldn't retrieve the list of message IDs")
    print(repr(e))
    print("This is a fatal error, exiting")
    print()
    exit()

  ###
  # display the headers and a delete prompt for each matching message
  # the prompt should help address concerns about deleting valid messages
  # note that unless skip-bin is provided, this moves the message to the Bin, allowing for recovery
  ###
  try:
    print()
    interesting_headers = [ "To", "From", "Subject", "Message-ID", "Cc", "Bcc"]
    acceptable_verify_resp = ['y', 'n']
    for a_message in messages:
      mid = a_message['id']
      verify = ''
      if no_confirm == True:
        verify = 'y'
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
