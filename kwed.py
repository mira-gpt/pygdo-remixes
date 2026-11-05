from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import re

BASE = 'https://remix.kwed.org/'
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_AUDIO_BYTES = 64 * 1024 * 1024


def kwed_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'remix.kwed.org' or parsed.username or parsed.password:
        raise ValueError('Kwed URL must stay on remix.kwed.org over HTTPS')
    return url


class KwedRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, kwed_url(newurl))


class Results(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.url = None
        self.title = []
        self.collect = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.url is None and tag == 'a' and 'download' in attrs.get('class', '').split():
            href = attrs.get('href', '')
            if re.fullmatch(r'/download\.php/\d+/[^?#]+\.mp3', href, re.IGNORECASE):
                self.url = kwed_url(urljoin(BASE, href))
                self.collect = True

    def handle_data(self, data):
        if self.collect:
            self.title.append(data)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.collect = False


def search(term: str) -> tuple[str, str]:
    term = ' '.join(term.split())
    if not term or len(term) > 100:
        raise ValueError('Search term must contain 1–100 characters')
    url = BASE + 'search/' + quote(term, safe='')
    request = Request(url, headers={'User-Agent': 'pygdo-remixes/0.1'})
    with build_opener(KwedRedirect()).open(request, timeout=15) as response:
        data = response.read(MAX_PAGE_BYTES + 1)
    if len(data) > MAX_PAGE_BYTES:
        raise ValueError('Kwed search response is too large')
    parser = Results()
    parser.feed(data.decode('utf-8', errors='replace'))
    if not parser.url:
        raise ValueError('No matching Kwed track found')
    return ''.join(parser.title).strip() or 'Kwed remix', parser.url


def download(url: str, path: Path) -> None:
    parsed = urlsplit(kwed_url(url))
    if not re.fullmatch(r'/download\.php/\d+/[^?#]+\.mp3', parsed.path, re.IGNORECASE) or parsed.query or parsed.fragment:
        raise ValueError('Invalid Kwed track URL')
    request = Request(url, headers={'User-Agent': 'pygdo-remixes/0.1'})
    with build_opener(KwedRedirect()).open(request, timeout=30) as response, path.open('xb') as output:
        total = 0
        while block := response.read(65536):
            total += len(block)
            if total > MAX_AUDIO_BYTES:
                raise ValueError('Kwed track is too large')
            output.write(block)
