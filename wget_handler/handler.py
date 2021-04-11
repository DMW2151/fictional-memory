# Lambda Function to download, unzip, and write pg_dump file of geospatial source to S3
# Sample Event:
# {
#     "body": {
#       "layername": "Wy-Places",
#       "path": "https://www2.census.gov/geo/tiger/TIGER2020/PLACE/tl_2020_56_place.zip"
#     }
# }

import json
import logging
import gzip
import boto3
import os
import subprocess
import botocore.config

# Initialize Loggers
logging.basicConfig(
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def create_s3_client():
    # Initialize S3 Connection
    try:
        client = boto3.client(
            's3', os.environ.get('AWS_DEFAULT_REGION'), 
            endpoint_url=os.environ.get('AWS_ENDPOINT_URL'),
            config=botocore.config.Config(s3={'addressing_style':'path'})
        )

    except Exception as err:
        logger.warning("Cannot Connect to S3\n", err)
        return None

    return client
    

def log_handler(bytestream, level=None):
    """ Logging utility, splits logstreams """
    if (bytestream == b'') or (bytestream is None):
        logger.info('Placeholder')
        return
    
    for logline in bytestream.split(b'\n'):
        # TODO: Wouldn't a switch statement be nice? Implement pseudo-switch!
        logger.info(logline)

def parse_api_gateway_event(event_request):
    """
    Wrapper for extracting content from POST body from
    API Gateway Event. Returns path (url of target) and 
    layername (table name)

    - event_request: dict: API Gateway Request Event
    """

    # Extract POST body from event request
    event = event_request.get('body', dict())

    path, layername = event.get('path'), event.get('layername')
    return path, layername


def s3_put_pgdump_object(client, sto, layername):
    """ Write stream of bytes to S3 """

    response = client.put_object(
        Bucket=os.environ.get('S3_DEFAULT_BUCKET'),
        Key=f'test/{layername}.dump',
        Body=gzip.compress(sto), 
    )


def handler(event, context):
    """
    Wrapper for DB table creation from a source URL. Requires GDAL bin and
    uses ogr2ogr's `/vsizip/` and `/vsistdout/` to process result, create a
    table in PG_DUMP format, and write PG_DUMP over to S3.

    - event: Json formatted data for function to process
    - context: AWS Lambda Context, required for handler func, this object
        provides methods and properties that provide information about
        the invocation, function, and execution environment.
    """

    path, layername = parse_api_gateway_event(event)
    if not (path and layername):
        # Return bad request - caller is missing at least one required param
        return {
            'statusCode': 422,
            'body': json.dumps('Expect Values for `Path` and `Layername'),
        }

    client = create_s3_client()
    if not client:
        return {
            'statusCode': 500,
            'body': json.dumps('S3 Connect Failed'),
        }


    # Call wget w. subprocess && download the target to /tmp/layer.zip
    # NOTE: subprocess.Popen doesn't work in emulator without proc.wait()
    proc = subprocess.Popen(
        ["wget", path, "--verbose", "-O", "/tmp/layer.zip"],
        stdout=subprocess.PIPE,
    )

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        return {
                'statusCode': 500,
                'body': json.dumps('Internal Status Error - Wget Timeout'),
        }

    # Transform /tmp/layer.zip to a PG_DUMP push the gzip result to S3
    # NOTE: /vsizip/vsistdin/ doesn't work in emulator, should work in 
    # production. Not sure if wrong version of ogr2ogr?? writing to /tmp/ isn't
    # that bad, leaving as /tmp/ write for now...
    dlps = subprocess.Popen([
            'ogr2ogr', '--config', 'PG_USE_COPY',  'YES',
            '-f', 'PGDump' , '/vsistdout/', '/vsizip//tmp/layer.zip',
            '-nln',     layername,
            '-t_srs',   'EPSG:4326',
            '-nlt',     'PROMOTE_TO_MULTI'],
        stdout=subprocess.PIPE,
    )

    # Wait on wget process to complete before proceeding &&
    # log errors from wget
    stdout, stderr = proc.communicate()
    log_handler(stdout)
    if stderr:
        log_handler(stderr)
        return {
            'statusCode': 500,
            'body': json.dumps('Internal Status Error - Proc'),
        }

    # Wait on ogr2ogr process to complete before proceeding &&
    # log errors from ogr2ogr
    
    # WARNING: The data read is buffered in memory, so do not use this method 
    # if the data size is large or unlimited. See the Docs! Careful when setting
    # bufsize too large! `dlsto` has potential to be giant.

    # NOTE: Don't bother with stderr on this one; proj spits out everything as an error 
    # including failed fopen() calls that don't affect output...
    
    try:
        dlsto, _ = dlps.communicate(timeout=5)
        dlps.wait()  
    except subprocess.TimeoutExpired:
        dlps.kill()
        return {
                'statusCode': 500,
                'body': json.dumps('Internal Status Error - Timeout'),
        }


    s3_put_pgdump_object(client, dlsto, layername)
    
    return {
            'statusCode': 200,
            'body': json.dumps({ 's3_path': f"{os.environ.get('S3_DEFAULT_BUCKET')}/test/{layername}.dump"}),
    }

