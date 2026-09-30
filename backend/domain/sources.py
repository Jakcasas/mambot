"""Source policy shared by answer and library workflows; never executes a URL."""
from urllib.parse import urlsplit

def trusted_source(value):
    if not isinstance(value, str) or any(ord(c) < 33 for c in value) or '\\' in value:
        return False
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or '').lower()
        return (parsed.scheme == 'https' and parsed.port in (None, 443)
                and parsed.username is None and parsed.password is None
                and (host == 'huit.edu.vn' or host.endswith('.huit.edu.vn')))
    except (ValueError, TypeError):
        return False
