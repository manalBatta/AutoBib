import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# ============================
# Helper functions
# ============================

def _split_concatenated(url):
    """Split multiple concatenated URLs"""
    lowers = url.lower()
    starts = [m.start() for m in re.finditer(r'https?://', lowers)]
    if len(starts) <= 1:
        return [url]
    parts = []
    for i, sidx in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(url)
        parts.append(url[sidx:end])
    return parts

def _trim_trailing_punct_and_balance(u):
    trailing_strip_chars = '.,;:!?\'"'
    u = u.rstrip(trailing_strip_chars)
    pairs = {')': '(', ']': '[', '}': '{'}
    while u and u[-1] in pairs:
        closer = u[-1]
        opener = pairs[closer]
        if u.count(opener) < u.count(closer):
            u = u[:-1]
        else:
            break
    return u

def _normalize_scheme(u):
    if u.lower().startswith('www.'):
        return 'http://' + u
    return u

def _clean_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    remove_keys = {
        'utm_source','utm_medium','utm_campaign','utm_term','utm_content',
        'fbclid','gclid','mc_cid','mc_eid','ref','page','offset',
        'sessionid','token','trk','feature','source'
    }
    cleaned_query = {k: v for k, v in query.items() if k.lower() not in remove_keys}
    new_query = urlencode(cleaned_query, doseq=True)
    cleaned = parsed._replace(query=new_query, fragment='')
    return urlunparse(cleaned)

# ============================
# Main extraction function
# ============================

def extract_urls(text):
    """
    Extract raw URLs from LaTeX text while ignoring URLs inside any LaTeX command.
    """
    # 1. Remove LaTeX comments
    text = re.sub(r'%.*', '', text)

    # 2. Remove all LaTeX commands with optional arguments
    # Matches \command{...} or \command[...]{...}
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{[^\}]*\}', '', text)

    # 3. Join broken URLs across lines
    text = re.sub(r'(https?://[^\s<>"\'\]\)]*)\n([^\s<>"\'\]\)]*)', r'\1\2', text)

    # 4. Regex to find raw URLs
    pattern = re.compile(r'(?i)(?:https?://|www\.)[^\s<>"\'\]\)]*', re.IGNORECASE)
    raw_matches = pattern.findall(text)

    results = []
    seen = set()

    for raw in raw_matches:
        for piece in _split_concatenated(raw):
            u = _trim_trailing_punct_and_balance(piece)
            u = _normalize_scheme(u)
            parsed = urlparse(u)
            if not parsed.netloc:
                continue
            normalized = urlunparse(parsed._replace(fragment=parsed.fragment))
            cleaned = _clean_url(normalized)
            if cleaned not in seen:
                seen.add(cleaned)
                results.append(cleaned)

    return results

# ============================
# Example test
# ============================


