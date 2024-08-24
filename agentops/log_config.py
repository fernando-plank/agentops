import logging
import os
import re
import sys


class AgentOpsLogFormatter(logging.Formatter):
    blue = "\x1b[34m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    prefix = "🖇 AgentOps: "

    FORMATS = {
        logging.DEBUG: f"(DEBUG) {prefix}%(message)s",
        logging.INFO: f"{prefix}%(message)s",
        logging.WARNING: f"{prefix}%(message)s",
        logging.ERROR: f"{bold_red}{prefix}%(message)s{reset}",
        logging.CRITICAL: f"{bold_red}{prefix}%(message)s{reset}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("agentops")
logger.propagate = False
logger.setLevel(logging.CRITICAL)

# Streaming Handler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(AgentOpsLogFormatter())
logger.addHandler(stream_handler)


# File Handler
class AgentOpsLogFileFormatter(logging.Formatter):
    def format(self, record):
        # Remove ANSI escape codes from the message
        record.msg = ANSI_ESCAPE_PATTERN.sub("", record.msg)
        return super().format(record)

# Custom Stream Handler to capture stdout and stderr


class StreamToLogger:
    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
        # Also write to the original stdout/stderr
        if self.log_level == logging.INFO:
            sys.__stdout__.write(buf)
        elif self.log_level == logging.ERROR:
            sys.__stderr__.write(buf)

    def flush(self):
        pass


ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
log_to_file = os.environ.get("AGENTOPS_LOGGING_TO_FILE", "True").lower() == "true"
if log_to_file:
    file_handler = logging.FileHandler("agentops.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    formatter = AgentOpsLogFileFormatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add handlers to the root logger without changing its level
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Add StreamHandler to root logger to capture stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(AgentOpsLogFormatter())
    root_logger.addHandler(stream_handler)

    # Redirect stdout and stderr to the logger
    sys.stdout = StreamToLogger(root_logger, logging.INFO)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR)
