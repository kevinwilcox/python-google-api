# required for the Google API
import api_info
import argparse
import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

# required to get the available cores (or total cores)
import os

# required for the timestamp in the name of the output file
import time
from datetime import datetime, timezone

# required for multiprocessor and multithread work
import threading
import multiprocessing
from queue import Queue
from threading import Thread

###
# write_output will write a single json object (a mail message) to the file and return to the calling thread
# since each thread will write to the file, it contains one object per line
# it does NOT contain an array of json objects!
###
def write_output(json_email, outfile):
  fh = open(outfile, 'a')
  fh.write(json_email)
  fh.close()
  return

###
# the use of globals is so user_list will always be appropriately parsed
# I suspect this is a problem based in my knowledge of python, not a problem with the language itself
#
# it iterates through the users list and creates a separate thread _per user_
# for small domains this is a minimal performance improvement
# for large domains (tested in 100k-mailbox domains), it's a ginormous improvement
# using queues ensures search_mail isn't waiting for a batch of threads to complete before starting the next thread
###
def make_threads(*user_list):
  global sa_creads
  global query
  global results_count
  global thread_count
  global outfile

  thread_queue = Queue(maxsize = thread_count)
  thread_queue.qsize()
  for i in range(thread_count):
    t = threading.Thread(name="worker_thread-%s" % i, target=search_mail, args=(thread_queue, sa_creds, query, results_count, outfile))
    t.start()
  for i in user_list:
    thread_queue.put(i)
  thread_queue.join()

###
# search_mail gets called once per thread
# it will pull a user ID from the queue, do a messages.list to see if any messages match the query and then messages.get for any matching message IDs
# if messages are retrieved via messages.get, it calls write_output to write those messages to a file as json objects
###
def search_mail(thread_queue, sa_creds, query, results_count, outfile):
  while True:
    current_user_id = thread_queue.get()
    print("searching mail for: " + current_user_id)
    ###
    # delegate as the current user id
    # in the Google logs, this looks like "<user> delegated access to token <token> for <scopes>"
    ###
    try:
      delegated = sa_creds.create_delegated(current_user_id)
      http_auth = delegated.authorize(httplib2.Http())
      service = discovery.build('gmail', 'v1', http=http_auth)
    except:
      print()
      print("Error: couldn't connect to Google, waiting two seconds and trying again")
      try:
        time.sleep(2)
        delegated = sa_creds.create_delegated(current_user_id)
        http_auth = delegated.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http_auth)
      except:
        print()
        print("Error: couldn't connect to Google a second time, waiting four seconds and trying again")
        try:
          delegated = sa_creds.create_delegated(current_user_id)
          http_auth = delegated.authorize(httplib2.Http())
          service = discovery.build('gmail', 'v1', http=http_auth)
        except Exception as e:
          print()
          print("Three errors connecting to Google as %s, exiting this thread" % current_user_id)
          fh = open('error_log-get_snippet', 'a')
          fh.write("error connecting as %s\n" % current_user_id)
          fh.write("%s" % repr(e))
          thread_queue.task_done()
          exit()

    ###
    # delegation was successful, perform the search as the current user
    # this returns message IDs, not messages, so it *should* be safe to store these in RAM
    ###
    try:
      messages = []
      results = service.users().messages().list(userId=current_user_id, q=query, maxResults=results_count).execute()
      if 'messages' in results:
        messages.extend(results.get('messages', []))
      while 'nextPageToken' in results:
        time.sleep(0.25)
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId=current_user_id, q=query, pageToken=page_token, maxResults=results_count).execute()
        messages.extend(results.gets('messages', []))
    except Exception as e:
      print()
      print("Error: could connect to Google but couldn't retrieve the list of message IDs")
      print(repr(e))
      print("This is a fatal error, exiting")
      print()
      thread_queue.task_done()
      exit()

    ###
    # iterate through the message IDs for the current user and retreive/display the corresponding message
    # note the headers displayed are arbitrary, long-term I want to add a --headers option and the SPF/DKIM/DMARC posture
    # as stated above, this does not store the actual message contents in RAM for the duration of the program, just the duration of the thread
    # if the message does not have ASCII content, the snippet field may not be populated
    ###
    try:
      for a_message in messages:
        mid = a_message['id']
        try:
          json_email = "{"
          msg_object = service.users().messages().get(userId=current_user_id,id=mid).execute()
          for a_header in msg_object['payload']['headers']:
            if a_header['name'] in ['To', 'From', 'Subject', 'Message-ID', 'Date']:
             json_email = json_email + "\"%s\": \"%s\"," % (a_header['name'], a_header['value'])
          json_email = json_email + "\"snippet\":\"%s\"}\n" % msg_object['snippet'].encode('utf-8', 'ignore')
          try:
            thread_delay = write_output(json_email, outfile)
          except:
            print("Error writing mail to the output file")
            print(repr(e))
            thread_queue.task_done()
            exit()
        except:
          print("Error: couldn't retrieve the message with ID %s, waiting two seconds and trying again" % mid)
          time.sleep(2)
          try:
            json_email = "{"
            msg_object = service.users().messages().get(userId=current_user_id,id=mid).execute()
            for a_header in msg_object['payload']['headers']:
              if a_header['name'] in ['To', 'From', 'Subject', 'Message-ID', 'Date']:
               json_email = json_email + "\"%s\": \"%s\"," % (a_header['name'], a_header['value'])
            json_email = json_email + "\"snippet\":\"%s\"}\n" % msg_object['snippet'].encode('utf-8', 'ignore')
            try:
              thread_delay = write_output(json_email, outfile)
            except Exception as e:
              print()
              print("Error writing mail to the output file")
              print(repr(e))
              thread_queue.task_done()
              exit()
          except Exception as e:
              fh = open('error_log-get_snippet', 'a')
              fh.write("error getting message %s as %s\n" % (mid, current_user_id))
              fh.write(repr(e))
              fh.close()
              thread_queue.task_done()
              exit()
    except Exception as e:
      print()
      print("Error: couldn't iterate through the message ID list")
      print(repr(e))
      print()
    thread_queue.task_done()

###
# if arguments can't be parsed then there is no use to continue
###
try:
  num_procs_available = len(os.sched_getaffinity(0))
except AttributeError:
  num_procs_available = os.cpu_count()

try:
  outfile = "found_messages-" + datetime.fromtimestamp(time.time(), tz = timezone.utc).replace(microsecond = 0).isoformat() + ".json"
  parser = argparse.ArgumentParser()
  parser.add_argument('--user', help="the complete email address to search; this must be an email address or 'any', there is no default", default = '')
  parser.add_argument('--infile', help="the file of email addresses to search, one per line; this is empty by default and not used if --user is set", default = '')
  parser.add_argument('--query', help="the string to search; for examples, see https://support.google.com/mail/answer/7190?hl=en", default = '')
  parser.add_argument('--threads', help="the number of threads to spawn for search; the default is 10", default = 10)
  parser.add_argument('--procs', help="the number of processes to spawn; the default is %s" % num_procs_available, default = num_procs_available)
  parser.add_argument('--results', help="the number of results to return per API request; the default (and max) is 500", default = 500)
  parser.add_argument('--outfile', help="the file to write to disk when messages are found; the default is %s" % outfile, default = outfile)
  args          = parser.parse_args()
  user_id       = args.user
  infile        = args.infile
  query         = args.query
  outfile       = args.outfile
  process_count = int(args.procs)
  thread_count  = int(args.threads)
  results_count = int(args.results)
except Exception as e:
  print("Error: couldn't assign the provided values")
  print(repr(e))
  print("This is a fatal error, exiting")
  print()
  exit()

###
# it may be safe to spawn a few more processes than the number of processers available but it's not recommended without testing
# if the user requested more processes than the number of processors available, verify that is correct
###
try:
  if process_count > num_procs_available:
    print()
    print("You have requested %s processes but there are only %s processors available." % (process_count, num_procs_available))
    verify = ''
    while verify not in ['y', 'Y', 'n', 'N']:
      verify = input("Please confirm with 'y' or 'n': ")
    if verify == 'y':
      pass
    else:
      print()
      process_count = int(input("How many processes do you wish to create? "))
except Exception as e:
  print()
  print("Error retrieving the number of processes to spawn.")
  print(repr(e))
  print("This is a fatal error, exiting")
  exit()
  
###
# --user is not optional at this point
###
if user_id == '' and infile == '':
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
elif infile != '':
  try:
    user_id_list = []
    users_file_fh = open(infile, 'r')
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
# here's where the arithmetic operations start getting...interesting
# the idea is to have <x> number of accounts fairly evenly divided into <y> threads
# that <y> threads value is determined by "thread_count"
# we have to make sure there aren't more threads than users
#   if thread_count is more than the number of users, set thread_count to total_users
###
total_users = len(user_id_list)
if total_users < thread_count:
  print("More threads requested than total users; setting thread count to %s" % (thread_count, total_users))
  thread_count = total_users

user_list = [list() for i in range(process_count)]
for i in range(total_users):
  offset = i % process_count
  user_list[offset].append(user_id_list[i])

###
# with the threads sorted, we can remove the user_id_list to reclaim memory
###
user_id_list = []

###
# the sequence is:
#   create a list of processes (where each process is made of <x> threads)
#   start each process
#   wait for all threads (and subsequently the processes) to finish (join())
### 
process_list = []
for i in range(process_count):
  process = multiprocessing.Process(target=make_threads, args=(user_list[i]))
  process_list.append(process)
for i in process_list:
  i.start()
for i in process_list:
  i.join()
print("done, exiting")
exit()
