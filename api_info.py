#!/usr/local/bin/python3.6
###
# the delegation email is primarily for the audit/reports API
# other APIs will require delegation by the actual account being
###
google_email  = "<email_address_for_delegation>"

###
# the secrets file is the json file from Google
# it will have the project name, an RSA key and more information
###
google_cfile  = "<client_secrets_json_file>"

###
# some APIs require either the domain or the customer ID
###
google_domain = "<domain_handled_by_Google>"

###
# these are the scopes approved in the advanced/API access part
#   of the security configuration
# example:
# google_scope = ['https://www.googleapis.com/auth/admin.reports.audit.readonly',
#                 'https://www.googleapis.com/auth/admin.reports.usage.readonly',
#                 'https://www.googleapis.com/auth/gmail.readonly']
###
google_scope  = ['<array_of_scopes>']
