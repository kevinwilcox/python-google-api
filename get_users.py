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
  parser.add_argument('--user', help="an optional email address to search for more info", default = '')
  parser.add_argument('--admin', help="boolean flag to request only admin users, default is false", action='store_true')
  parser.add_argument('--deleted', help="the complete email address to search; the default is all", action='store_true')
  parser.add_argument('--superadmin', help="boolean flag to request only superadmin users, default is false", action='store_true')
  parser.add_argument('--count', help="the number of results to return per API request, default is the max of 500; note this is not the total count of results to retrieve, it is the max the script will fetch per request; the script will continue requesting until all users are returned", default = 500)
  args                = parser.parse_args()
  user_email          = args.user
  admin_only          = args.admin
  max_results         = args.count
  show_deleted        = args.deleted
  super_admin_only    = args.superadmin
except Exception as e:
  print("Error: couldn't determine whether to retrieve deleted users")
  print(repr(e))
  print("This is a fatal error, exiting")
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

try:
  search_string = ''
  domain_users = []
  if user_email != '':
      search_string = "email:" + user_email
  if admin_only == True:
    if search_string == '':
      search_string = "isDelegatedAdmin=true"
    else:
      search_string += " AND isDelegatedAdmin=true"
  if super_admin_only == True:
    if search_string == '':
      search_string = "isAdmin=true"
    else:
      search_string += " AND isAdmin=true"
  results = service.users().list(domain=api_info.google_domain, orderBy='email', showDeleted=show_deleted, query=search_string, maxResults = max_results).execute()
  if 'users' in results:
    domain_users.extend(results.get('users', []))
  while 'nextPageToken' in results:
    time.sleep(0.25)
    page_token = results['nextPageToken']
    results = service.users().list(domain=api_info.google_domain, orderBy='email', showDeleted=show_deleted, query=search_string, maxResults = max_results, pageToken = page_token).execute()
    domain_users.extend(results.get('users', []))
except Exception as e:
  print("Error: connected to Google but couldn't retrieve user list")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  for a_user in domain_users:
    print()
    print("User record")
    print("User's id: " + a_user['id'])
    print("User's name: " + a_user['name']['fullName'])
    print("User is suspended: " + str(a_user['suspended']))
    print("User email address: " + a_user['primaryEmail'])
    print("User last logged in: " + a_user['lastLoginTime'])
except Exception as e:
  print("Error: couldn't iterate through the activity list")
  print(repr(e))
print()
exit()
