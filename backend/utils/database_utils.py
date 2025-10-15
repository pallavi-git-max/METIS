"""
Database utility functions to handle SQLite locking issues
"""
import time
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

def retry_on_locking_error(max_retries=3, delay=1):
    """
    Decorator to retry database operations on SQLite locking errors
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e).lower() or "e3q8" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Database locked on attempt {attempt + 1}, retrying in {delay}s...")
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(f"Database locked after {max_retries} attempts")
                            raise
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    raise
            return None
        return wrapper
    return decorator

def safe_db_operation(operation_func, *args, **kwargs):
    """
    Safely execute a database operation with retry logic
    """
    max_retries = 3
    delay = 1
    
    for attempt in range(max_retries):
        try:
            return operation_func(*args, **kwargs)
        except OperationalError as e:
            if "database is locked" in str(e).lower() or "e3q8" in str(e):
                if attempt < max_retries - 1:
                    logger.warning(f"Database locked on attempt {attempt + 1}, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Database locked after {max_retries} attempts")
                    raise
            else:
                raise
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
    
    return None
