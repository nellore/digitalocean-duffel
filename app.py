#!/usr/bin/env python3
"""
duffel.py

Flask app for routing to Rail/Monorail outputs on various hosts.

Privacy / data-minimization notes
---------------------------------
Duffel logs one line per successful redirect:

    date (UTC, YYYY-MM-DD) [TAB] pseudonym [TAB] resource [TAB] path

* No IP addresses are stored. The pseudonym is an HMAC-SHA256 of the
  client IP keyed with a secret that lives only on the server (see
  DUFFEL_LOG_SECRET / the key file below), truncated to 24 hex chars.
  Without the secret, the pseudonym cannot be matched against a list of
  candidate IPs.
* The secret is mixed with the current year (YYYY), so a pseudonym is
  stable within a calendar year -- enough to count unique visitors per
  day/week/month/year -- but cannot be linked across years.
* Only the date is recorded, never the time of day.
* Requests that do not resolve to a real file (404s) are logged with the
  path replaced by "-", so arbitrary probe strings never reach the log.
* Optionally, log files older than DUFFEL_LOG_RETENTION_DAYS are deleted
  at startup.

See analytics.py for computing hit/unique-visitor counts from these logs.
"""
from flask import Flask, redirect, render_template, abort, request, Response
import requests
import gzip
import atexit
import os
import time
import hmac
import hashlib
import random
app = Flask(__name__)

# Path to log file is hardcoded
# DO NOT STORE IPs/LOCATIONS/TIMES OF DAY; see module docstring
# Always open new logfile when restarting
_LOGDIR = os.path.expanduser('~/recount2_logs')
os.makedirs(_LOGDIR, exist_ok=True)

# Length of the pseudonym in hex characters (96 bits)
_PSEUDONYM_LEN = 24

def _load_secret():
    """ Loads logging secret from env or key file; creates key file if absent.

        The secret must never be committed to the repo or shared with the
        logs. Deleting the key file makes all existing pseudonyms
        permanently unmatchable.

        Return value: secret as bytes
    """
    env_secret = os.environ.get('DUFFEL_LOG_SECRET')
    if env_secret:
        return env_secret.encode('utf-8')
    keyfile = os.path.join(_LOGDIR, 'duffel_secret')
    try:
        # O_EXCL so concurrent gunicorn workers don't race to create it
        fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as keystream:
            keystream.write(os.urandom(32))
    except FileExistsError:
        pass
    with open(keyfile, 'rb') as keystream:
        return keystream.read()
_SECRET = _load_secret()

def _prune_old_logs():
    """ Deletes log files older than DUFFEL_LOG_RETENTION_DAYS (0 = keep all).

        No return value.
    """
    try:
        retention_days = int(os.environ.get('DUFFEL_LOG_RETENTION_DAYS', '0'))
    except ValueError:
        retention_days = 0
    if retention_days <= 0:
        return
    cutoff = time.time() - retention_days * 86400
    for filename in os.listdir(_LOGDIR):
        if 'recount_log' not in filename:
            continue
        path = os.path.join(_LOGDIR, filename)
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass
_prune_old_logs()

filename_numbers = []
for filename_number in [filename.split('.')[1] for filename
    in os.listdir(_LOGDIR) if 'recount_log' in filename]:
    try:
        filename_numbers.append(int(filename_number))
    except ValueError:
        # Not a recognized log file
        pass
try:
    new_filename_number = max(filename_numbers) + 1
except ValueError:
    # Starting from 0 here
    new_filename_number = 0
_LOGFILE = os.path.join(_LOGDIR,
        'recount_log.{filename_number}.{rando}.tsv.gz'.format(
        filename_number=new_filename_number,
        rando='{rando}'.format(rando=random.random())[2:]
    ))
_LOGSTREAM = gzip.open(_LOGFILE, 'at')
def close_log():
    """ Closes log stream; for use on script exit.

        No return value.
    """
    _LOGSTREAM.close()
atexit.register(close_log)

def pseudonym(ip, year):
    """ Computes year-scoped keyed pseudonym for an IP.

        ip: client IP as string
        year: 'YYYY' string

        Return value: hex string of length _PSEUDONYM_LEN
    """
    message = (year + '\n' + ip).encode('utf-8')
    return hmac.new(_SECRET, message, hashlib.sha256).hexdigest()[
                                                            :_PSEUDONYM_LEN]

def log_access(resource, identifier):
    """ Writes one minimized log line.

        resource: a given resource, like "recount3"
        identifier: relative path to file, or "-" if request did not resolve

        No return value.
    """
    now = time.gmtime()
    ip = str(request.headers.get('X-Forwarded-For',
                        request.remote_addr)).split(',')[0].strip()
    print('\t'.join(
        [time.strftime('%Y-%m-%d', now),
             pseudonym(ip, time.strftime('%Y', now)),
             resource,
             identifier]), file=_LOGSTREAM, flush=True)

_PRIVACY_NOTICE = (
    'Duffel is your friendly neighborhood data broker. '
    'To report aggregate usage of recount, Duffel records the date (not '
    'time) of each successful redirect, the file requested, and a keyed '
    'pseudonym of the requesting IP that rotates yearly. IP addresses '
    'are not stored.'
)

@app.route('/')
def duffout():
    return _PRIVACY_NOTICE

@app.route('/<resource>/<path:identifier>')
def forward(resource, identifier):
    """ Redirects request for file to direct URL.

        resource: a given resource, like "recount2"
        identifier: relative path to file or directory

        Return value: Flask redirect response object
    """
    if resource == 'recount3':
        idies_url = '/'.join(
                    ['https://recount-opendata.s3.amazonaws.com/recount3/release', identifier]
                )
        idies_response = requests.head(idies_url)
        if idies_response.status_code == 200:
            log_access(resource, identifier)
            return redirect(idies_url, code=302)
    elif resource == 'recount':
        # Redirect to IDIES URL in order of descending version
        for i in ['2']: # add versions to precede 2 as they are released
            if identifier.startswith(' '.join(['v', i, '/'])):
                idies_url = '/'.join(
                            ['https://recount-opendata.s3.amazonaws.com/recount2', identifier]
                        )
                idies_response = requests.head(idies_url)
                if idies_response.status_code == 200:
                    log_access(resource, identifier)
                    return redirect(idies_url, code=302)
        # v1 is not explicitly versioned
        idies_url = '/'.join(['https://recount-opendata.s3.amazonaws.com/recount2', identifier])
        idies_response = requests.head(idies_url)
        if idies_response.status_code == 200:
            log_access(resource, identifier)
            return redirect(idies_url, code=302)
    # Unresolved requests: count them, but never store the requested path
    log_access(resource if resource in ('recount', 'recount3') else '-', '-')
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)
