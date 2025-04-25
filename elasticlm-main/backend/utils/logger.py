import logging
import sys
import traceback
from pythonjsonlogger import jsonlogger

# Configuration
ENABLE_MULTILINE_TRACE = True  # Set to False to disable multi-line stack trace logging

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def process_log_record(self, log_record):
        exc_info = log_record.get("exc_info")
        if exc_info and isinstance(exc_info, tuple):
            log_record['stack_trace'] = self.formatException(exc_info)
        else:
            log_record['stack_trace'] = None
        return log_record

class MultiLineStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            if ENABLE_MULTILINE_TRACE and record.exc_info:
                stream.write("\n--- Stack Trace ---\n")
                traceback.print_exception(*record.exc_info, file=stream)
                stream.write("\n")
            self.flush()
        except Exception:
            self.handleError(record)

# Create a logger
logger = logging.getLogger("ElasticLM")
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Prevent duplicate logging

# Create a handler that writes to stdout
logHandler = MultiLineStreamHandler(sys.stdout)
logHandler.setLevel(logging.DEBUG)

formatter = CustomJsonFormatter(
    '%(asctime)s %(levelname)s %(message)s %(module)s %(lineno)d %(funcName)s %(filename)s stack_trace'
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Example usage (can be removed in production)
try:
    raise ValueError("Example error for testing stack trace")
except Exception as e:
    logger.error("Error occurred", exc_info=sys.exc_info())
