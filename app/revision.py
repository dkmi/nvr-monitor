"""Build identity is generated locally; never committed as its own commit SHA."""
import json,re
from pathlib import Path

def installed_revision():
    try:
        revision=json.loads(Path(__file__).with_name('build.json').read_text()).get('revision')
        return revision if isinstance(revision,str) and re.fullmatch('[0-9a-f]{40}',revision) else None
    except (OSError,ValueError):return None
