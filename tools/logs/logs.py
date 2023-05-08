import inspect
import logging
import logging.config
    
"""
Default logging configuration
"""
LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s | %(filename)s | %(asctime)s | %(message)s", # Example: [INFO:     | app.py | 2022-06-03 20:59:59 | Dummy Info]
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    'handlers': {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr"
        },
    },
    'loggers': {
        '': {
            "handlers": ["default"],
            'propagate': True,
        },
    }
}

def get_logger(name:str=inspect.stack()[1].filename, log_level=None) -> logging.Logger:
    """Sets up logger using default Simple API configurations

    Args:
        name (str): Name of logger, typically __name__

    Returns:
        logging.Logger: Returns a ready to use logger
    """

    # Load logging config
    logging.config.dictConfig(LOGGING_CONFIG)

    # Ensure root log level set
    logging.getLogger().setLevel(log_level)

    # Get logger
    logger = logging.getLogger(name)

    # Return logger
    return logger