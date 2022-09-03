# Stub file for future i18n
from string import Template


def gettext(message, _lang=None, **kwargs):
    return Template(message).safe_substitute(**kwargs)
