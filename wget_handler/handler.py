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

# Initialize S3 Connection
client = boto3.client(
    's3', os.environ.get('AWS_DEFAULT_REGION'), 
    config=botocore.config.Config(s3={'addressing_style':'path'})
)

# Initialize Loggers
logging.basicConfig(
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def log_handler(bytestream, level=None):
    """ Logging utility, splits logstreams """
    if (bytestream == b'') or (bytestream is None):
        logger.info(b'Placeholder')
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


def s3_put_pgdump_object(sto, layername):
    """ Write stream of bytes to S3 """

    response = client.put_object(
        Bucket=os.environ.get('S3_DEFAULT_BUCKET'),
        Key=f'test/{layername}.dump'
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

    # Call wget w. subprocess && download the target to /tmp/layer.zip
    proc = subprocess.Popen(
        ["wget", path, "--verbose", "-O", "/tmp/layer.zip"],
        stdout=subprocess.PIPE,
    )
    
    # Transform /tmp/layer.zip to a PG_DUMP push the gzip result to S3
    # NOTE: /vsizip/vsistdin/ should work here, not sure if wrong version of 
    # ogr2ogr; writing to /tmp/ isn't that bad though...
    dlps = subprocess.Popen([
            'ogr2ogr', '--config', 'PG_USE_COPY',  'YES',
            '-f', 'PGDump' , '/vsistdout/', '/vsizip//tmp/layer.zip',
            '-nln',     layername,
            '-t_srs',   'EPSG:4326',
            '-nlt',     'PROMOTE_TO_MULTI'],
        stdin=proc.stdout,
        stdout=subprocess.PIPE,
        bufsize=8192,
    )

    # Wait on wget process to complete before proceeding &&
    # log errors from wget
    _, stderr = proc.communicate()
    if stderr:
        log_handler(stderr)
        return {
            'statusCode': 500,
            'body': json.dumps(stderr.__str__()),
        }

    # Wait on ogr2ogr process to complete before proceeding &&
    # log errors from ogr2ogr
    #
    # WARNING: The data read is buffered in memory, so do not use this method 
    # if the data size is large or unlimited. See the Docs! Careful when setting
    # bufsize too large! `dlsto` has potential to be giant.
    dlsto, stderr = dlps.communicate()    
    if stderr:
        log_handler(stderr)
        return {
            'statusCode': 500,
            'body': json.dumps(stderr.__str__()),
        }

    s3_put_pgdump_object(dlsto, layername)
    
    return {
            'statusCode': 200,
            'body': json.dumps({ 's3_path': f"{os.environ.get('S3_DEFAULT_BUCKET')}/test/{layername}.dump"}),
        }
