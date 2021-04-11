import subprocess
import logging
import pytest
import requests
import re
import io
import handler as pgh

# Initialize Loggers
logging.basicConfig(
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

@pytest.fixture
def configure_test_logger():

    # Initialize Loggers - Temp
    s = io.StringIO()

    logging.basicConfig(
        format='%(asctime)s-%(levelname)s-%(message)s',
        level=logging.INFO,
    )

    console = logging.StreamHandler(s)
    logger = logging.getLogger()

    logger.addHandler(
        console
    )

    return s


def test_psql_layer():
    ps = subprocess.Popen(
        ['psql', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    try:
        sto, sterr = ps.communicate(timeout=1)

        # Check that there are no errors on version check        
        assert sterr.decode('utf-8') == ''

        # Check that there is a valid version w. postgres client 11+
        # should be 11.2 at time of writing...
        assert re.search('1[0-9].\d', sto.decode('utf-8')) is not None

    except subprocess.TimeoutExpired:
        log.error('subprocess.TimeoutExpired - Placeholder')
        raise Exception('subprocess.TimeoutExpired - Placeholder')

def test_logging_handler_null_byte(configure_test_logger):
    pgh.log_handler(b'')
    configure_test_logger.seek(0)
    assert configure_test_logger.getvalue() == ''

def test_logging_handler_singleline(configure_test_logger):
    pgh.log_handler('One')
    configure_test_logger.seek(0)
    assert configure_test_logger.getvalue() == 'One\n'

def test_logging_handler_multiline(configure_test_logger):
    pgh.log_handler('One\nTwo\nThree')
    configure_test_logger.seek(0)
    assert configure_test_logger.getvalue() == 'One\nTwo\nThree\n'

def test_write_tmpfile_missing_file():
    confirmed_fp = pgh.write_dump_to_tmpfile(
        'dmw2151-placeholder', 'test/This_File_Doesnt_Exist.dump'
    )
    assert confirmed_fp is None

def test_write_tmpfile_present_file():
    confirmed_fp = pgh.write_dump_to_tmpfile(
        'dmw2151-placeholder', 'test/GuamBlocks.dump'
    )
    assert confirmed_fp is not None
    
def test_restore_func_file():
    """
    curl -XPOST  \
        --data "@./test/requests/guam.json" \
        "http://localhost:9001/2015-03-31/functions/function/invocations"
    """
    with open('/var/task/test_events/guam.json', 'r') as fi:
        guam = fi.read()
        r = requests.post(
            'http://localhost:9001/2015-03-31/functions/function/invocations', 
            data=guam
        )

def test_restore_func_missing_file():
    """
    curl -XPOST  \
        --data "@./test/requests/guam.json" \
        "http://localhost:9001/2015-03-31/functions/function/invocations"
    """
    with open('/var/task/test_events/missing.json', 'r') as fi:
        guam = fi.read()
        r = requests.post(
            'http://localhost:8080/2015-03-31/functions/function/invocations', 
            data=guam
        )
