import logging
import logging.config


# TODO: move to common.utils.logging
def get_logger(name: str = None):
    """Getting configured logger"""
    return logging.getLogger(name or "app")


# TODO: move to common.utils.logging
def log_message(exc, error_data, level=logging.ERROR):
    """
    Helps to log caught errors by exception handler
    """
    logger = get_logger(__name__)

    error_details = {
        "error": error_data.get("error", "Unbound exception"),
        "details": error_data.get("details", str(exc)),
    }
    message = "{exc.__class__.__name__} '{error}': [{details}]".format(exc=exc, **error_details)
    logger.log(level, message, exc_info=(level == logging.ERROR))
