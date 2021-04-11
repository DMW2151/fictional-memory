# Lambda Function that's triggered on S3 Upload; Takes a pg_dump file and pushes to DB...

import gzip
import json
import logging
import os
import subprocess
import urllib.parse
import tempfile

import botocore.config
import botocore.execeptions
import boto3

# Initialize S3 connection with default region, addressing style + custom 
# `endpoint_url` (for testing)
s3 = boto3.resource(
    's3', 
    os.environ.get('AWS_DEFAULT_REGION'), 
    endpoint_url=os.environ.get('AWS_ENDPOINT_URL'),
    config=botocore.config.Config(s3={'addressing_style':'path'})
)

# Initialize Default logger...
logging.basicConfig(
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log_handler(logstream):
    """
    Logging utility, converts logs to str, splits into individual lines, 
    and writes to logger
    """

    if type(logstream) == bytes:
        logstream = logstream.decode('utf-8')

    if logstream in ('', None):
        return
    
    # TODO: Wouldn't a switch statement be nice? Implement pseudo-switch later,
    # for now, just check regex for `error` in the msg/line...
    for logline in logstream.split():        
        if re.search('error', logline, re.IGNORECASE):
            logger.error(logline)
        else:
            logger.info(logline)
        

def parse_s3_trigger_event(event):
    """
    Parse content of AWS S3 Event, return a key and bucket name 
    for S3 download target
    """

    try:
        # NOTE: AWS Example/Docs here, only access the first record, assume that
        # this is safe because events are ONLY coming from the S3 Trigger.
        bucket = event['Records'][0]['s3']['bucket']['name']
        
        key = urllib.parse.unquote_plus(
            event['Records'][0]['s3']['object']['key'], encoding='utf-8'
        )

    # For local/dev testing, In case user sends bad mock-up of AWS S3 Event...
    except (KeyError, IndexError) as err:
        logger.error(err)
        return None, None

    return bucket, key

def write_dump_to_tmpfile(bucket, key):
    """
    Download pg_dump file from S3 and save to generated /tmp/ file
    """

    # Check for errors in AWS S3 Credential Errors, etc, making no 
    # distinction which Botocore error is thrown, most often NoCredentials
    try:
        obj = s3.Object(bucket_name=bucket, key=key)
        b = obj.get()["Body"]

    except (botocore.exceptions.BotoCoreError)  as e:
        logger.error(e)
        return None
        
    # Write results from s3 -> /tmp/xxx.sql; decompressing while writing, 
    # use the os.open() to access bytes written instead of relying on higher 
    # level open(). Checks for count b/c a file that's just b'' will not throw
    # OSError
    with tempfile.NamedTemporaryFile(suffix='.sql') as tmpf:
        fd = os.open(tmpf.name, os.O_RDWR)    
        try:
            r = os.write(fd, gzip.decompress(b.read()))
            if r > 0:
                return tmpfp.name
            else:
                logger.error('No Bytes Written...')
                return None

        # Typically thrown for non-gzipped file, e.g. if b.read() gives 
        # b'I am Not A GZIP', gzip  throws OSError
        except OSError as err: 
            logger.error(err)            
            return None


def handler(event, context):
    """
    Wrapper for ingesting pg_dump file from S3 -> EC2/RDS

    - event: Json formatted data for function to process
    - context: AWS Lambda Context, required for handler func, this object
        provides methods and properties that provide information about
        the invocation, function, and execution environment.
    """
    
    bucket, key = parse_s3_trigger_event(event)
    if not (bucket and key):
        # Return bad request - caller is missing at least one required param
        return {
            'statusCode': 422,
            'body': json.dumps('Expect AWS S3 Event Request'),
        }

    # TODO: Should be able to refactor this to stream w.o write to /tmp/
    # Download the and gunzizp pg_dump file to file and then write to psql
    # aws s3 cp s3://sample_bucket/test/sample.dump - |\
    #   psql -h $PG_HOST -d $PG_DATABASE -U $PG_USER -f file.sql
    try:
        restore_fp = write_dump_to_tmpfile(bucket, key)
        if not restore_fp:
            return {
                'statusCode': 500,
                'body': json.dumps('Failed to Create File...'),
            }
         
        # Use subprocess check_call to wait on execution of pg_restore
        psql_exit_code = subprocess.check_call([
                'psql', '-h', os.environ.get('PG_HOST'), 
                        '-d', os.environ.get('PG_DATABASE'), 
                        '-U', os.environ.get('PG_USER'),
                        '-f', restore_fp,
            ]
        )
            
    except subprocess.CalledProcessError as err:
        log_handler(err.__str__())
        return { 
            'statusCode': 500, 
            'body': json.dumps(err.__str__()),
        }

    return {
            'statusCode': 200,
            'body': json.dumps(
                {
                    's3_path': f"{os.environ.get('S3_DEFAULT_BUCKET')}/{key}",
                }
            ),
        }

