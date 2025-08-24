import os
from redis import Redis
from rq import Queue

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', os.getenv('REDIS_URL', 'redis://localhost:6379').split('://')[1].split(':')[0] if '://' in os.getenv('REDIS_URL', 'redis://localhost:6379') else 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Queue names
PDF_QUEUE_NAME = 'pdf_generation'
DEFAULT_QUEUE_NAME = 'default'

# Job timeout settings (in seconds)
JOB_TIMEOUT = 300  # 5 minutes
RESULT_TTL = 86400  # 24 hours
FAILURE_TTL = 86400  # 24 hours

def get_redis_connection():
    """Get Redis connection instance"""
    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )

def get_queue(name=PDF_QUEUE_NAME):
    """Get RQ Queue instance"""
    redis_conn = get_redis_connection()
    return Queue(name, connection=redis_conn)

def get_pdf_queue():
    """Get PDF generation queue"""
    return get_queue(PDF_QUEUE_NAME)