# python-google-api

This is a collection of scripts targeted primarily at incident responders in organisations using G Suite (also called Google Apps for Business/Education/Nonprofits).  They are written using a python 3.x environment, currently python 3.6.

The following python modules are either required (and are available via pip):

httplib2
google-api-python-client
oauth2client

Additionally, some scripts use:

os
json
base64
argparse

They assume you already have a service account and oauth2 credentials file from Google.  The name of that file can be set in "api_creds.py".  By default each script imports api_creds to read configuration details.

There is no default interpreter set because I call the python executable and pass the script name as an argument.  If you want to run each script separate of the interpreter then you'll need to add the default interpreter and set the script as executable (if using Unix or Linux).

As the license states, I take zero responsibility if you destroy your environment or if you over-step your authority and use them in a way that gets you fired.  Please python responsibly.
