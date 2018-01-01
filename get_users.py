import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

try:
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="an optional email address to search for more info", default = '')
  parser.add_argument('--admin', help="boolean flag to request only admin users, default is false", action='store_true')
  parser.add_argument('--deleted', help="the complete email address to search; the default is all", action='store_true')
  parser.add_argument('--superadmin', help="boolean flag to request only superadmin users, default is false", action='store_true')
  args                = parser.parse_args()
  user_email          = args.user
  admin_only          = args.admin
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
  results = service.users().list(domain=api_info.google_domain, orderBy='email', showDeleted=show_deleted, query=search_string).execute()
  domain_users = results.get('users', [])
except Exception as e:
  print("Error: connected to Google but couldn't retrieve user list")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()

try:
  for a_user in domain_users:
    print()
    print("User record")
    print("User's name: " + a_user['name']['fullName'])
    print("User is suspended: " + str(a_user['suspended']))
    print("User email address: " + a_user['primaryEmail'])
    print("User last logged in: " + a_user['lastLoginTime'])
except Exception as e:
  print("Error: couldn't iterate through the activity list")
  print(repr(e))
print()
exit()
