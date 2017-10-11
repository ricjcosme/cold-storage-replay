import logging
import gzip
import re
import os
from os import environ
import requests
import time
import sys

import boto
from boto.s3.connection import S3Connection
from boto.s3.connection import OrdinaryCallingFormat

from multiprocessing import Pool

if environ.get('AWS_ACCESS_KEY') is None:
    sys.exit("No AWS_ACCESS_KEY defined, stopping execution.")

if environ.get('AWS_SECRET_ACCESS_KEY') is None:
    sys.exit("No AWS_SECRET_ACCESS_KEY defined, stopping execution.")

if environ.get('S3_BUCKET') is None:
    os.environ['S3_BUCKET'] = "cold-storage.s3.example.com"

if environ.get('S3_BUCKET_REGION') is None:
    os.environ['S3_BUCKET_REGION'] = "eu-west-1"

if environ.get('S3_BUCKET_PATH') is None:
    os.environ['S3_BUCKET_PATH'] = "daily"

if environ.get('REPLAY_TO_DOMAIN') is None:
    os.environ['REPLAY_TO_DOMAIN'] = "http://localhost:8080"

if environ.get('LOG_FILE_INPUT_DIR') is None:
    os.environ['LOG_FILE_INPUT_DIR'] = "/tmp"

if environ.get('LOG_FILE_PATTERN') is None:
    os.environ['LOG_FILE_PATTERN'] = "2017"

if environ.get('LOG_FILE_CHUNK_LINES') is None:
    os.environ['LOG_FILE_CHUNK_LINES'] = "4"

if environ.get('OUTPUT_LOGGING_FILE') is None:
    os.environ['OUTPUT_LOGGING_FILE'] = os.environ['LOG_FILE_INPUT_DIR'] + "/" \
                                        + str(int(time.time())) + "_replay.log"

logging.basicConfig(format='%(asctime)s %(message)s',
                    filename=os.environ['OUTPUT_LOGGING_FILE'],
                    filemode='w', level=logging.INFO)

headers = {
    'User-Agent': "cold-storage-replay",
    'X-Original-Timestamp': "",
}

fmt = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) - (?P<body>.+)(["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""", re.IGNORECASE)
pattern = '%d/%b/%Y:%H:%M:%S +0000'


def process_log_file(l):
    data = re.search(fmt, l)
    if data:
        datadict = data.groupdict()
        ip = datadict["ipaddress"]
        datetimestring = datadict["dateandtime"]
        url = datadict["url"]
        bytessent = datadict["bytessent"]
        referrer = datadict["refferer"]
        useragent = datadict["useragent"]
        status = datadict["statuscode"]
        method = data.group(6)
        body = datadict["body"]
        if method == "POST":
            headers['X-Original-Timestamp'] = str(int(time.mktime(time.strptime(datetimestring, pattern))))
            r = requests.post(os.environ['REPLAY_TO_DOMAIN'] + url.replace(" ", ""),
                              data=body.decode('string_escape'), headers=headers)
            logging.info(str(r.status_code) + " " + datetimestring + " " + url)


try:
    if '.' in os.environ['S3_BUCKET']:
        conn = boto.s3.connect_to_region(region_name=os.environ['S3_BUCKET_REGION'],
                                         aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
                                         aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                                         calling_format=OrdinaryCallingFormat())
    else:
        conn = S3Connection(os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(os.environ['S3_BUCKET'])
    for l in bucket.list():
        if os.environ['LOG_FILE_PATTERN'] in str(l.key):
            l.get_contents_to_filename(os.environ['LOG_FILE_INPUT_DIR'] + "/"
                                       + str(l.key).replace(os.environ['S3_BUCKET_PATH'] + "/", ""))

    for f in os.listdir(os.environ['LOG_FILE_INPUT_DIR']):
        if f.endswith(".gz"):
            logfile = gzip.open(os.environ['LOG_FILE_INPUT_DIR'] + "/" + f, "r")
        elif f.endswith(".log"):
            logfile = open(os.environ['LOG_FILE_INPUT_DIR'] + "/" + f, "r")
        else:
            continue
        pool = Pool()
        for l in logfile:
            pool.map(process_log_file,
                     logfile,
                     chunksize=int(os.environ['LOG_FILE_CHUNK_LINES']))
        logfile.close()
except Exception as e:
    logging.error(e)
