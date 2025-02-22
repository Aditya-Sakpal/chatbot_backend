import logging
import time
import os
from datetime import datetime
import functools

import psutil

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

log_dir = os.path.join(project_root, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger("project_logger")
logger.setLevel(logging.INFO)

log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_performance(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        This function logs the performance of the decorated function
        Args:
            func : function : The function to be decorated
            *args : tuple : The arguments to be passed to the function
            **kwargs : dict : The keyword arguments to be passed to the function
        Returns:
            result : any : The result of the function
        """
        
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 ** 2)  # Memory in MB

        result = func(*args, **kwargs)

        end_time = time.time()
        end_memory = process.memory_info().rss / (1024 ** 2)  # Memory in MB

        execution_time = end_time - start_time
        memory_used = end_memory - start_memory

        logger.info(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        logger.info(f"Memory used: {memory_used:.4f} MB")

        return result

    return wrapper