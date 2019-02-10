# python-google-api

This is a collection of scripts targeted primarily at incident responders in organisations using G Suite (also called Google Apps for Business/Education/Nonprofits).  They are written using a python 3.x environment, currently python 3.6.

Scripts use the following modules available in any default python installation:

 - os
 - time
 - json
 - base64
 - argparse
 - datetime

Additionally, they use the following modules that are available via pip:

 - httplib2
 - oauth2client
 - google-api-python-client

Every script assumes you already have a service account and oauth2 credentials file from Google.  The name of that file can be set in "api_info.py".  By default each script imports api_info to read configuration details.

Each script has its own set of required scopes.  As I add scripts or functionality to existing scripts, I will document the scopes they need in the individual script.  I will always opt for the scope with the least privilege - if an API has a .readonly scope that accomplishes what I need, I'll use that instead of a scope with the ability to modify settings.

At this point I have functionality that requires some combination of the following:

-- to read and modify/delete mail
https://mail.google.com/
https://www.googleapis.com/auth/gmail.modify

-- to read mail (no modify/delete)
https://www.googleapis.com/auth/gmail.readonly

-- to pull reports and audit items
https://www.googleapis.com/auth/admin.reports.audit.readonly
https://www.googleapis.com/auth/admin.reports.usage.readonly
https://www.googleapis.com/auth/apps/reporting/audit.readonly

-- to read users from the directory
https://www.googleapis.com/auth/admin.directory.user.readonly

-- the Alert Centre may have information about suspicious activity, this allows one to read those alerts
https://www.googleapis.com/auth/apps.alerts

There is no default interpreter set because I call the python executable and pass the script name as an argument.  If you want to run each script separate of the interpreter then you'll need to add the default interpreter and set the script as executable (if using Unix or Linux).

As the license states, I take zero responsibility if you destroy your environment or if you over-step your authority and use them in a way that gets you fired.  Please python responsibly.
