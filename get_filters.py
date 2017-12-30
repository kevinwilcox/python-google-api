import api_info
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

userID = <email_address_to_search>

sa_creds = ServiceAccountCredentials.from_json_keyfile_name(api_info.google_cfile, api_info.google_scope)
delegated = sa_creds.create_delegated(api_info.google_email)
http_auth = delegated.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http_auth)
results = service.users().settings().filters().list(userId=userID).execute()
filters = results.get('filter', [])
for a_filter in filters:
  crit = a_filter['criteria']
  action = a_filter['action']
  print()
  print("filter found: " + a_filter['id'])
  if 'from' in crit:
    print("  -- filter requires from: " + crit['from'])
  if 'to' in crit:
    print("  -- filter requires to: " + crit['to'])
  if 'subject' in crit:
    print("  -- filter requires subject: " + crit['subject'])
  if 'query' in crit:
    print("  -- filter requires 'includes words': " + crit['query'])
  if 'negatedQuery' in crit:
    print("  -- filter requires 'doesn\'t have': " + crit['negatedQuery'])
  if 'hasAttachment' in crit and crit['hasAttachment'] == True:
    print("  -- filter requires an attachment")
  if 'excludeChats' in crit and crit['excludeChats'] == True:
    print("  -- filter excludes chats/hangouts")
  if 'size' in crit and crit['sizeComparison'] == 'larger':
    print("  -- filter requires size greater than " + crit['size'])
  elif 'size' in crit and crit['sizeComparison'] == 'smaller':
    print("  -- filter requires size smaller than " + crit['size'])

  if 'addLabelIds' in action:
    print("  -- filter adds the following labels: " + action['addLabelIds'])
  if 'removeLabelIds' in action:
    print("  -- filter removes the following labels: " + action['removeLabelIds']) 
print()
print("no remaining filters")
print()
exit()
