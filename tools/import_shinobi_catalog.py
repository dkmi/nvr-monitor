"""Build the RTSP picker data from saved public Shinobi Hub manufacturer pages.

Supply a directory of HTML files named after the URL-encoded manufacturer slug
(e.g. Hikvision.html or TP-Link%20VIGI.html). No network requests are made here.
"""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

# Keep only templates that point at the host entered by the administrator.
TEMPLATE = re.compile(r'rtsp://(?:_USERNAME_:_PASSWORD_@)?_ADDRESS_(?::([0-9]+))?([/?][!-~]*)?', re.I)
H264 = re.compile(r'h[. _-]?264|avc1', re.I)
H265 = re.compile(r'h[. _-]?265|hevc', re.I)
SENSITIVE_PATH = re.compile(r'(?:user(?:name)?|pass(?:word)?|pwd|token|secret|key)=', re.I)
EMBEDDED_AUTH = re.compile(r'(?<=/)user=[^/?&]*?_password=[^/?&]*?(?=_channel=)', re.I)
QUERY_AUTH = re.compile(r'([?&])(user(?:name)?|pass(?:word)?|pwd)=[^&]*', re.I)


class StreamRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.cells = None
        self.cell = None
        self.url = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cells, self.url = [], None
        elif tag == 'td' and self.cells is not None:
            self.cell = []
            self.url = dict(attrs).get('data-url', self.url)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.cells.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr' and self.cells is not None:
            if self.url:
                self.rows.append((self.cells, self.url))
            self.cells = None


def rtsp_address(template):
    match = TEMPLATE.fullmatch(template.strip())
    if not match:
        return None
    port = int(match[1] or 554)
    path = match[2] or '/'
    path = re.sub(r'\[channel\]', '[CHANNEL]', path, flags=re.I)
    path = EMBEDDED_AUTH.sub('user=[USERNAME]_password=[PASSWORD]', path)
    path = QUERY_AUTH.sub(lambda m: f'{m[1]}{m[2]}=[{"USERNAME" if m[2].lower().startswith("user") else "PASSWORD"}]', path)
    checked_path = re.sub(r'\[(CHANNEL|USERNAME|PASSWORD)\]', '', path)
    # Remaining sensitive parameters have no corresponding input in the form.
    checked_params = re.sub(r'(?:user(?:name)?|pass(?:word)?|pwd)=\[(?:USERNAME|PASSWORD)\]', '', path, flags=re.I)
    if (not 1 <= port <= 65535 or len(path) > 2048 or
            re.search(r'[\\#\[\]{}<>]|%(?![0-9a-fA-F]{2})', checked_path) or
            re.search(r'_[A-Z]{2,}_', checked_path) or SENSITIVE_PATH.search(unquote(checked_params))):
        return None
    if path.startswith('?'):
        path = '/' + path
    return port, path


def rows_for_file(file):
    brand = unquote(file.stem).strip()
    page = StreamRows()
    page.feed(file.read_text(encoding='utf-8'))
    known = set()
    model_rows = []
    for cells, url in page.rows:
        address = rtsp_address(url)
        if not address or H265.search(address[1]):
            continue
        if len(cells) == 3 and H264.fullmatch(cells[0]):
            known.add(address)
        elif len(cells) == 4 and cells[0]:
            model_rows.append((cells[0], cells[1], address))

    def entry(model, address):
        port, path = address
        return {'brand': brand, 'model': model, 'port': port, 'path': path}

    for address in sorted(known):
        yield entry('', address)
    for model, kind, address in model_rows:
        # Shared uploads usually say only "rtsp". Require either a matching
        # labeled path or an explicit H.264 marker in the shared entry.
        if address in known or H264.fullmatch(kind) or H264.search(address[1]):
            yield entry(model, address)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pages', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    entries = {}
    for file in sorted(args.pages.glob('*.html')):
        for entry in rows_for_file(file):
            key = (entry['brand'].casefold(), entry['model'].casefold(), entry['path'], entry['port'])
            entries.setdefault(key, entry)
    with args.output.open('w', encoding='utf-8') as output:
        output.write('[\n')
        output.write(',\n'.join('  ' + json.dumps(entries[key], ensure_ascii=False, separators=(',', ':'))
                               for key in sorted(entries)))
        output.write('\n]\n')
    print(f'{len(entries)} streams across {len({key[0] for key in entries})} manufacturers')


if __name__ == '__main__':
    main()
