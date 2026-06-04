from shared.logging_config import setup_logging

setup_logging()

from consumer import start_consumer

start_consumer()