# python-google-api

This is a collection of scripts targeted primarily at incident responders in organisations using G Suite (also called Google Apps for Business/Education/Nonprofits).  They are written using a python 3.x environment, currently python 3.6.

List of scripts and their functions (alphabetical):

o change_mail_labels.py
GMail uses "labels", not "folders", so a single message may have multiple labels associated with it. For example, a newly received email message may have both the INBOX and UNREAD labels. This script allows you to change those labels as necessary - for example, to search for email messages that fit a specific pattern, remove the INBOX label and add the SPAM label. By default it removes INBOX and UNREAD and adds SPAM; it will display the labels being removed and added, and it will prompt for each change.

o delete_messages.py
There are two ways to delete messages, via either an explicit delete API call or by changing its label to "TRASH". This script calls the built-in delete API and, depending on preference, may either "bin"/"TRASH" a message or perform a true delete (similar to a user deleting a message and emptying their bin). By default it will prompt for every delete.

o get_auth.py
This script retrieves authentication logs for a domain; by default it will pull all authentication logs for the last week. It displays the logs to screen.

o get_drive_item_permissions.py
This takes a user's email address and returns all items in Drive that the user can access; it was intended to be used to help quickly identify the scope of a potential data breach where credentials were lost and you need to know which files those credentials can access.

o get_filters.py
It is common for attackers to add email filters so that messages from IT and other groups will be automatically deleted or sent to the attacker for evasion and recon purposes. This script will return all filters associated with a given user's email address.

o get_labels.py
I wrote this script because of a scenario where a group of actors made the same new "folder"/"label" in every mailbox they compromised and it was useful to know when specific labels, or labels similarly structured, showed up in the domain. It returns all labels (folders) for the given user's email address.

o get_snippet_from_search.py
This script takes an email address (or the "any" keyword) and a search string, then it returns common headers and the first few lines of ASCII/printable text from all matching messages. If the "any" keyword is used then it first will search the entire Google Directory for the domain and retrieve all email addresses for the domain, then sequentially searches each mailbox (be warned, if you have thousands of accounts it takes approximately 22 minutes to search 2000 mailboxes).

o get_team_drive_events.py
Team Drives are interesting because they don't have an "owner" like other Drive types. This script is really designed to look for create and delete events so that TDs can be paired with an individual/account.

o get_team_drives.py
This is the original version of the above script. It looks for create events. I need to remove it.

o get_users.py
This uses the Directory API to retrieve all of the users in the domain's Directory. It will show the user's internal Google ID number, their name, email address, suspended status and last login timestamp.

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
