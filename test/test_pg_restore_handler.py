import subprocess
import logging
import re

# Initialize Loggers
logging.basicConfig(
    format='%(asctime)s-%(levelname)s-%(message)s'
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def test_psql_version():
    ps = subprocess.Popen(
        ['psql', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    try:
        sto, sterr = ps.communicate(timeout=1)
        
        # Check that there are no errors on version check        
        assert sterr.decode('utf-8') == ''

        # Check that there is a valid version w. postgres client 11+
        # should be 11.2 at time of writing...
        assert re.search('11.\d', sto.decode('utf-8')) is not None

    except subprocess.TimeoutExpired:
        log.error('subprocess.TimeoutExpired - Placeholder')
        raise Exception('subprocess.TimeoutExpired - Placeholder')


def test_logging_handler():
    pass


def test_write_tmpfile_missing_file():
    pass


def test_write_tmpfile_regular_file():
    pass


def test_restore_func_missing_file():
    pass


def test_restore_func_present_file():
    pass

