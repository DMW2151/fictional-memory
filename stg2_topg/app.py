# Lambda Function that's triggered on S3 Upload; Takes a pg_dump file and pushes to DB...

import json
import logging
import boto3
import botocore.config
import sys
import gzip
import os
import subprocess
import gzip
import urllib.parse
import io

# Initialize S3 Connection

s3 = boto3.resource(
    's3', os.environ.get('AWS_DEFAULT_REGION'), 
    config=botocore.config.Config(s3={'addressing_style':'path'})
)

# Initialize Loggers
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_handler(bytestream, level=None):
    for logline in bytestream.split(b'\n'):
        # TODO: Wouldn't a switch statement be nice? Implement pseudo-switch!
        logger.error(logline)

def parse_s3_trigger_event(event):
    """
    Parse content of `event` to get bucket name for S3 download
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8'
    )

    if (bucket and key):
        return bucket, key

    else:
        return None, None
    

def handler(event, context):
    """
    Wrapper for ingesting pg_dump file from S3 -> EC2 

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
            'body': json.dumps('Expect Values for `Path` and `Layername'),
        }
    

    # Download the pg_dump file and stream through gzip and then to psql
    # Equiv. Call...
    # 
    # aws s3 cp s3://sample_bucket/test/sample.dump - |\
    #   gunzip - |\
    #   psql -h $PG_HOST -d $PG_DATABASE -U $PG_USER
    
    logger.info('1OK!')
    # Pipe S3 -> Stdout
    obj = s3.Object(
        bucket_name=bucket,
        key=key
    )
    logger.info('2OK!')
    
    a = obj.get()["Body"].read()
    print(len(a))
    a = gzip.decompress(a)
    print(len(a))
    
    
    logger.info('3OK!')
    # Pipe Stdin -> PSQL on EC2/RDS
    try:
        logger.info("psql....")

        with open("/tmp/f1.txt", 'wb+') as fd:
            fd.write(a)
            logger.info('4OK!')
            
            _ = subprocess.call([
                    'psql', '-h', os.environ.get('PG_HOST'), 
                            '-d', os.environ.get('PG_DATABASE'), 
                            '-U', os.environ.get('PG_USER'),
                            '-f', '/tmp/f1.txt'
                ],
            )
            logger.info('5OK!!!')
    
    except subprocess.CalledProcessError as err:
        log_handler(err)
        return { 'statusCode': 500, 'body': json.dumps(err.__str__()) }

    return {
            'statusCode': 200,
            'body': json.dumps(
                {
                    's3_path': f"{os.environ.get('S3_DEFAULT_BUCKET')}/{key}",
                    'restored': 'True'
                }
            ),
        }
