"""Local HVSC SID discovery; no playback or network access."""
from pathlib import Path


def metadata(path: Path):
    """Read title and author from a PSID/RSID header when present."""
    with path.open('rb') as source:
        header = source.read(118)
    if len(header) < 118 or header[:4] not in (b'PSID', b'RSID'):
        return '', ''
    def text(data):
        return data.split(b'\0', 1)[0].decode('latin-1', errors='replace').strip()
    return text(header[22:54]), text(header[54:86])


def search(root: Path, query: str, limit=100):
    query = query.strip().casefold()
    if not query or limit < 1:
        raise ValueError('Provide a nonempty SID search')
    root = root.resolve(strict=True)
    results = []
    for path in root.rglob('*'):
        if path.suffix.lower() != '.sid' or not path.is_file():
            continue
        try:
            resolved = path.resolve(strict=True)
            relative = resolved.relative_to(root).as_posix()
            title, author = metadata(resolved)
        except (OSError, ValueError):
            continue
        if query in ' '.join((relative, title, author)).casefold():
            results.append((relative, title, author))
    results.sort(key=lambda row: row[0].casefold())
    return results[:limit]


SESSION_KEY = 'remixes.sid.search'


def remember_search(session, query, results):
    """Keep the exact numbered snapshot in the active PyGDO session."""
    session.set(SESSION_KEY, {'query': query, 'results': [list(row) for row in results]})


def select_result(session, number):
    entry = session.get(SESSION_KEY)
    if not isinstance(entry, dict) or not isinstance(entry.get('results'), list):
        raise ValueError('No SID search in this session; search first')
    results = entry['results']
    if number < 1 or number > len(results):
        raise ValueError('SID result number is out of range')
    row = results[number - 1]
    if not isinstance(row, (list, tuple)) or len(row) != 3 or not all(isinstance(x, str) for x in row):
        raise ValueError('Invalid SID search result; search again')
    return row
