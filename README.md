Cold Storage Replay
======

Open cold storage archived logfiles in AWS S3, parse and replay each request against the same or a new server.

This is a simple python script that relies on env vars definiton. Those are:
- AWS_ACCESS_KEY - AWS Access Key ID (ref. [here](http://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys))
- AWS_SECRET_ACCESS_KEY - AWS Secret Access Key (ref. [here](http://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys))
- S3_BUCKET - name of the S3 bucket where the cold storage archives are (default: "cold-storage.s3.example.com")
- S3_BUCKET_REGION - S3's AWS region 
- S3_BUCKET_PATH - internal bucket path to files (it any) (default: "daily")
- REPLAY_TO_DOMAIN - host / domain to send requests to (default: "http://localhost:8080")
- LOG_FILE_INPUT_DIR - where to put the downloaded archived cold storage files (default: "/tmp")
- LOG_FILE_PATTERN - a pattern to match on the files' name otherwise all are processed (default: "2017")
- LOG_FILE_CHUNK_LINES - number of lines to parse and process at a time on each parallel worker (default: 4)

## Python, libs and environment:
Python version: 2.7.*

Requirements available at: [requirements.txt](requirements.txt) (pip usage recommended): 
   
    pip install -r requirements.txt
    
Virtualenv usage recommended:
https://virtualenv.pypa.io/en/stable/

## Usage:

```
git clone https://github.com/ricjcosme/cold_storage_replay.git
cd cold_storare_replay
# open vars, fill AWS_ACCESS_KEY and AWS_SECRET_ACCESS_KEY, change any other values accordingly and source it:
. ./vars
# run:
python replay.py
```

## Notes:
Don't forget to provision enough storage.
The more vCPUs the machine has, the better - "pool = Pool()" retrieves the number of available CPU cores by default)
