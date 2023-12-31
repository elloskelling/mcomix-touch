""" i18n.py - Encoding and translation handler."""

import gettext
import io
import locale
import os
import pkgutil
import sys

try:
    import chardet
except ImportError:
    chardet = None

from mcomix import preferences
from mcomix import portability
from mcomix import constants

# Translation instance to enable other modules to use
# functions other than the global _() if necessary
_translation = None

def to_unicode(string):
    """Convert <string> to unicode. First try the default filesystem
    encoding, and then fall back on some common encodings.
    """
    if isinstance(string, str):
        return string

    # Try chardet heuristic
    if chardet:
        probable_encoding = chardet.detect(string)['encoding'] or \
            locale.getpreferredencoding() # Fallback if chardet detection fails
    else:
        probable_encoding = locale.getpreferredencoding()

    for encoding in (
        probable_encoding,
        sys.getfilesystemencoding(),
        'utf-8',
        'latin-1'):

        try:
            ustring = str(string, encoding)
            return ustring

        except (UnicodeError, LookupError):
            pass

    return string.decode('utf-8', 'replace')

def to_utf8(string):
    """ Helper function that converts unicode objects to UTF-8 encoded
    strings. Non-unicode strings are assumed to be already encoded
    and returned as-is. """

    if isinstance(string, str):
        return string.encode('utf-8')
    else:
        return string

def install_gettext(force_lang=None):
    """ Initialize gettext with the correct directory that contains
    MComix translations. This has to be done before any calls to gettext.gettext
    have been made to ensure all strings are actually translated. """

    # Add the sources' base directory to PATH to allow development without
    # explicitly installing the package.
    sys.path.append(constants.BASE_PATH)

    # Initialize default locale
    locale.setlocale(locale.LC_ALL, '')

    if force_lang is not None:
        lang = force_lang
        lang_identifiers = [lang]
    elif preferences.prefs['language'] != 'auto':
        lang = preferences.prefs['language']
        lang_identifiers = [ lang ]
    else:
        # Get the user's current locale
        lang = portability.get_default_locale()
        lang_identifiers = gettext._expand_lang(lang)

    # Make sure GTK uses the correct language.
    os.environ['LANGUAGE'] = lang

    domain = constants.APPNAME.lower()

    # Search for .mo files manually, since gettext doesn't support packaged resources
    for lang in lang_identifiers:
        resource = os.path.join('messages', lang, 'LC_MESSAGES', '%s.mo' % domain)
        try:
            translation_content = pkgutil.get_data('mcomix', resource)
        except FileNotFoundError:
            pass
        else:
            fp = io.BytesIO(translation_content)
            translation = gettext.GNUTranslations(fp)
            break
    else:
        translation = gettext.NullTranslations()

    global _translation
    _translation = translation

def get_translation() -> gettext.NullTranslations:
    """Returns the loaded translation instance.
    (gettext.GNUTranslations is a subclass of NullTranslations.)"""
    return _translation or gettext.NullTranslations()

def _(message: str) -> str:
    """Translate the messsage using the current translator."""
    return get_translation().gettext(message)

def to_display_string(string):
    """ Converts a string to a valid UTF-8 string at the expense of data accuracy. """
    return string.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')

# vim: expandtab:sw=4:ts=4
