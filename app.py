#!/usr/bin/env python3
"""
duffel.py

Flask app for routing to Rail/Monorail outputs on various hosts.
"""
from flask import Flask, redirect, render_template, abort, request, Response
from contextlib import closing
import subprocess
import json
import requests
import sys
import gzip
import atexit
import os
import time
import mmh3
import random
app = Flask(__name__)

# Path to log file is hardcoded
# DO NOT TRACK IPs/LOCATIONS; track only times
# Always open new logfile when restarting
_LOGDIR = os.path.expanduser('~/recount2_logs')
os.makedirs(_LOGDIR, exist_ok=True)
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

@app.route('/')
def duffout():
    return "Duffel is your friendly neighborhood data broker."

@app.route('/<resource>/<path:identifier>')
def forward(resource, identifier):
    """ Redirects request for file to direct URL.

        Requires global "paths" dictionary is active. 

        resource: a given resource, like "recount2"
        identifier: relative path to file or directory

        Return value: Flask redirect response object
    """
    # Log all requests, even weird ones
    ip = str(request.headers.get('X-Forwarded-For',
                        request.remote_addr)).split(',')[0].strip()
    print('\t'.join(
        [time.strftime('%A, %b %d, %Y at %I:%M:%S %p %Z'),
             str(mmh3.hash128(ip + 'recountsalt')),
             resource,
             identifier]), file=_LOGSTREAM, flush=True)
    if resource == 'recount3':
        idies_url = '/'.join(
                    ['https://recount-opendata.s3.amazonaws.com/recount3/release', identifier]
                )
        idies_response = requests.head(idies_url)
        if idies_response.status_code == 200:
            return redirect(idies_url, code=302)
    elif resource == 'recount':
        # Redirect to IDIES URL in order of descending version
        for i in ['2']: # add versions to precede 2 as they are released
            if identifier.startswith(' '.join(['v', i, '/'])):
                idies_url = '/'.join(
                            ['https://sciserver.org/public-data/recount2/data', identifier]
                        )
                idies_response = requests.head(idies_url)
                if idies_response.status_code == 200:
                    return redirect(idies_url, code=302)
        # v1 is not explicitly versioned
        idies_url = '/'.join(['https://sciserver.org/public-data/recount2/data', identifier])
        idies_response = requests.head(idies_url)
        if idies_response.status_code == 200:
            return redirect(idies_url, code=302)
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)
