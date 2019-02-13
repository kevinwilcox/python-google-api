import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

###
# if arguments can't be parsed then there is no use to continue
###
try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; this must be an email address or 'any', there is no default", default = '')
  parser.add_argument('--list', help="the file of email addresses to search, one per line; this is empty by default and not used if --user is set", default = '')
  parser.add_argument('--query', help="the string to search; for examples, see https://support.google.com/mail/answer/7190?hl=en", default = '')
  args      = parser.parse_args()
  user_id   = args.user
  u_file    = args.list
  query     = args.query
except Exception as e:
  print("Error: couldn't assign the provided values")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

###
# --user is not optional at this point
###
if user_id == '' and u_file == '':
  print()
  print("No user was provided.")
  print("Please re-run with --user <>, where the username is the user's complete email address")
  print("Exiting...")
  print()
  exit()

###
# --query is optional but not providing a search string could result in a massive amount of mail being returned!
###
if query == '':
  print()
  print("No query string was provided. This will return all email for that user.")
  print("Please review https://support.google.com/mail/answer/7190?hl=en and see if you wish to provide a query string.")
  print("Are you sure you want to continue with no query string?")
  verify = ''
  while verify != 'y' and verify != 'Y' and verify != 'n' and verify != 'N':
    verify = input("Please respond with 'y' or 'n': ")
  if verify == 'y' or verify == 'Y':
    pass
  else:
    print()
    query = input("Please provide the query string to use: ")

###
# sa_creds will be used every time a delegation occurs but the service account needs to be authenticated
###
sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)

###
# if operating on "any":
#   retrieve all users in the domain, sorted by email address
#   store all domain email addresses in a list
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
# --list is optional but can save several minutes if you have several thousands (or tens/hundreds of thousands) of users in your domain
###
elif u_file != '':
  try:
    user_id_list = []
    users_file_fh = open(u_file, 'r')
    for a_line in users_file_fh.readlines():
      user_id_list.append(a_line.strip('\n'))
  except Exception as e:
    print()
    print("Error reading email addresses from file")
    print(repr(e))
    print("This is a fatal error, exiting")
    print()
    exit() 

###
# for this to be true, --user was specified and it was not set to "any"
# the rest of the script expects a list of email addresses, if an address was provided then this saves that address into a one-item list
###
else:
  user_id_list = [user_id]

###
# iterate through the users list, searching mail as it goes
# currently, the script displays mail as it moves from user to user
# for simple searches this is my desired behaviour because:
#   it allows to stop the search if the query looks too broad
#   it doesn't store the content of all of the messages in RAM
###
for current_user_id in user_id_list:
  print()
  print("searching mail for: " + current_user_id)
  ###
  # delegate as the current user id
  # in the Google logs, this looks like "<user> delegated access to token <token> for <scopes>"
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
  # delegation was successful, perform the search as the current user
  # this returns message IDs, not messages, so it *should* be safe to store these in RAM
  # I have not tested this with searches with hundreds of thousands (or millions) of results...
  #   -- if anyone with large domains wants to test this and let me know how it performs, I'd be awfully grateful!
  ###
  try:
    messages = []
    results = service.users().messages().list(userId=current_user_id, q=query).execute()
    if 'messages' in results:
      messages.extend(results.get('messages', []))
    while 'nextPageToken' in results:
      time.sleep(0.25)
      page_token = results['nextPageToken']
      results = service.users().messages().list(userId=current_user_id, q=query, pageToken=page_token).execute()
      messages.extend(results.gets('messages', []))
  except Exception as e:
    print()
    print("Error: could connect to Google but couldn't retrieve the list of message IDs")
    print(repr(e))
    print("This is a fatal error, exiting")
    print()
    exit()

  ###
  # iterate through the message IDs for the current user and retreive/display the corresponding message
  # note the headers displayed are arbitrary, long-term I want to add a --headers option and the SPF/DKIM/DMARC posture
  # as stated above, this does not store the actual message contents in RAM
  # if the message does not have ASCII content, the snippet field may not be populated
  ###
  try:
    print()
    for a_message in messages:
      mid = a_message['id']
      try:
        msg_object = service.users().messages().get(userId=current_user_id,id=mid).execute()
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
