###
# necessary scopes
# changing message labels can be accomplished with:
#   https://www.googleapis.com/auth/gmail.modify
# it can also be accomplished with the more-permissive:
#   https://mail.google.com
# I do not recommend this unless you are 100% sure you need to do this
###

import time
import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

acceptable_verify_resp = ['y', 'n']

###
# error and exit if the command-line arguments can't be assigned
# --skip-confirm will re-label messages without any confirmation
#   this is a fairly dangerous thing to do so...you're warned
###
try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; this must be an email address or 'any', there is no default", default = '')
  parser.add_argument('--query', help="the string to search; for examples, see https://support.google.com/mail/answer/7190?hl=en", default = '')
  parser.add_argument('--no-confirm', help="WARNING DANGER WARNING this option skips prompting for label confirmation", dest='no_confirm', action='store_true')
  parser.add_argument('--remove', help="""the labels to remove, separated by a comma: --remove "INBOX,FOO,FOO2", the default is INBOX""", dest='to_remove', default = 'INBOX')
  parser.add_argument('--add', help="""the labels to add, separated by a comma: --add "SPAM,READ,FOO", the default is SPAM""", dest='to_add', default="SPAM")
  args              = parser.parse_args()
  user_id           = args.user
  query             = args.query
  skip_confirm      = args.no_confirm
  labels_to_add     = args.to_add
  labels_to_remove  = args.to_remove

except Exception as e:
  print("Error: couldn't assign the provided values")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

try:
  verify = ''
  while verify not in acceptable_verify_resp:
    print()
    print("You have chosen to remove the following labels:")
    print()
    for a_label in labels_to_remove.split(','):
      print(a_label)
    print()
    verify = input("Are these the correct labels to remove, 'y' or 'n'? ").lower()
  if verify == 'n':
    print()
    print("Please re-run this script with the labels you wish to remove")
    print()
    exit()

except Exception as e:
  print()
  print("Error: could not determine labels to remove")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

try:
  verify = ''
  while verify not in acceptable_verify_resp:
    print()
    print("You have chosen to add the following labels:")
    print()
    for a_label in labels_to_add.split(','):
      print(a_label)
    print()
    verify = input("Are these the correct labels to add, 'y' or 'n'? ").lower()
  if verify == 'n':
    print()
    print("Please re-run this script with the labels you wish to add")
    print()
    exit()

except Exception as e:
  print()
  print("Error: could not determine labels to add")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

###
# any move to SPAM should require a search string
# failing to provide a string would prompt for every email to be moved to SPAM
###
if query == '':
  print()
  print("No query string was provided. This is a required field.")
  print("Please re-run with --query <>, where the query string follows https://support.google.com/mail/answer/7190?hl=en")
  print("Exiting...")
  print()
  exit()

###
# any move to SPAM should require a userid
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
  # display the headers and a SPAM prompt for each matching message
  # the prompt should help address concerns about SPAMming valid messages
  # note that this does not delete anything, so users can always move the
  #   message back to their Inbox
  ###
  try:
    print()
    interesting_headers = [ "To", "From", "Subject", "Message-ID", "Cc", "Bcc"]
    for a_message in messages:
      mid = a_message['id']
      verify = ''
      if skip_confirm == True:
        verify = 'y'
      try:
        msg_object = service.users().messages().get(userId=current_user_id,id=mid).execute()
        for a_header in msg_object['payload']['headers']:
          if a_header['name'] in interesting_headers:
            print(a_header['name'] + " is: " + a_header['value'])
        print()
        while verify not in acceptable_verify_resp:
          verify = input("Do you want to move this message from %s to %s, 'y' or 'n'? " % (labels_to_remove, labels_to_add)).lower()
        if verify == 'y':
          print()
          print("You chose yes, labels will be changed to %s" % labels_to_add)
          try:
            msg_labels = { 'removeLabelIds':[labels_to_remove], 'addLabelIds':[labels_to_add] }
            modified_msg = service.users().messages().modify(userId=current_user_id, id=mid, body=msg_labels).execute()
            print()
            print("Modify request sent, continuing")
            print()
          except Exception as e:
            print()
            print("Error modifying this message")
            print("Error message: " + repr(e))
            print("This is not a fatal error, continuing")
            print()
        else:
          print()
          print("You chose no, skipping this message")
          print()
        print()
      except Exception as e:
        print()
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
