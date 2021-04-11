# Lambda Function that's triggered on S3 Upload; Takes a pg_dump file and pushes to DB...

import gzip
import json
import logging
import os
import subprocess
import urllib.parse

import botocore.config
import boto3

# Initialize S3 Connection
s3 = boto3.resource(
    's3', os.environ.get('AWS_DEFAULT_REGION'), 
    endpoint_url=os.environ.get('AWS_ENDPOINT_URL'),
    config=botocore.config.Config(s3={'addressing_style':'path'})
)

# Initialize Loggers
logging.basicConfig(
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_handler(bytestream, level=None):
    """ Logging utility, splits logstreams """
    if (bytestream == b'') or (bytestream is None):
        logger.info(b'Placeholder')
        return
    
    for logline in bytestream.split(b'\n'):
        # TODO: Wouldn't a switch statement be nice? Implement pseudo-switch!
        logger.info(logline)

def parse_s3_trigger_event(event):
    """
    Parse content of  AWS S3 Event to get key and bucket name for S3 download
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], 
        encoding='utf-8'
    )

    if (bucket and key):
        return bucket, key

    else:
        return None, None
    

def write_dump_to_tmpfile(bucket, key):
    """
    Download S3 pg_dump file and save to /tmp/
    """

    ## Access S3 File; ensure exists before read
    try:
        obj = s3.Object(bucket_name=bucket, key=key)
        b = obj.get()["Body"]
        logger.info('Get', bucket, key)
    ## Placeholder for errors in AWS S3 Credential Errors, etc.
    except Exception as e:
        logger.error(e) 
        

    # Write results from s3 -> /tmp/xxx.sql; decompressing
    # while writing, 
    with open("/tmp/layer.sql", 'wb+') as fd:
        try:
            fd.write(gzip.decompress(b.read()))

        # Placeholder for errors, might run into invalid 
        # gzip file, file might not be available, etc...
        except: 
            raise NotImplementedError


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
    

    # Download the pg_dump file and stream through gzip and then to psql
    # Equiv. Call...    
    # aws s3 cp s3://sample_bucket/test/sample.dump - |\
    #   gunzip - |\
    #   psql -h $PG_HOST -d $PG_DATABASE -U $PG_USER
    try:
        write_dump_to_tmpfile(bucket, key)
        
        # Use subprocess run
        psql_exit_code = subprocess.check_call([
                'psql', '-h', os.environ.get('PG_HOST'), 
                        '-d', os.environ.get('PG_DATABASE'), 
                        '-U', os.environ.get('PG_USER'),
                        '-f', '/tmp/layer.sql'
            ]
        )
            
    except subprocess.CalledProcessError as err:
        log_handler(err.__str__().encode('utf-8'))
        return { 
            'statusCode': 500, 
            'body': json.dumps(err.__str__().encode('utf-8')),
            'CalledProcessCode': psql_exit_code,
        }

    return {
            'statusCode': 200,
            'body': json.dumps(
                {
                    's3_path': f"{os.environ.get('S3_DEFAULT_BUCKET')}/{key}",
                }
            ),
        }

