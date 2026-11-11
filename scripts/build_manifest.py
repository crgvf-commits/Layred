#!/usr/bin/env python3
"""Generate/check SHA-256 of every tracked repository file except this manifest itself."""
from pathlib import Path
import hashlib
import sys

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'audit/SHA256SUMS.txt'

def sha(f):
    h=hashlib.sha256()
    with f.open('rb') as fh:
        for block in iter(lambda:fh.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and p!=MANIFEST
                  and '__pycache__' not in p.parts and '.git' not in p.parts)

lines=[f'{sha(p)}  {p.relative_to(ROOT).as_posix()}' for p in files()]
content='\n'.join(lines)+'\n'
if '--check' in sys.argv:
    if not MANIFEST.exists():
        print('Manifest not found',file=sys.stderr);sys.exit(1)
    if MANIFEST.read_text(encoding='utf-8')!=content:
        print('SHA256 VERIFICATION FAILED: files changed, missing, or added',file=sys.stderr)
        sys.exit(1)
    print(f'SHA256 VERIFIED: {len(lines)} files, no additions or modifications')
else:
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    MANIFEST.write_text(content,encoding='utf-8')
    print(f'Wrote hashes for {len(lines)} files to {MANIFEST}')
