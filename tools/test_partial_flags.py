#!/usr/bin/env python3
"""Check feature flag combinations against a copied live partial record."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

source = Path('/old-config/partial-albums/1367549.json')
state = json.loads(source.read_text())
original_record = source.read_bytes()
target = Path(state['target'])
files = [p for p in target.rglob('*') if p.is_file() and p.suffix.lower() in {'.mp3','.flac','.m4a','.opus'}]
checksums = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
helper = '/test-patch/root/scripts/partial_albums.py'
expected_ids = [t['id'] for t in state['missing']]
for retain, retry in [('false','false'), ('false','true'), ('true','false'), ('true','true')]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / 'partial-albums'; root.mkdir()
        record = root / '1367549.json'
        copy = dict(state); copy['next_retry'] = 0
        record.write_text(json.dumps(copy))
        original = record.read_bytes()
        env = dict(os.environ, RETAIN_PARTIAL_ALBUMS=retain, RETRY_MISSING_TRACKS=retry, PARTIAL_RETRY_HOURS='24')
        due = subprocess.check_output(['python3',helper,'--root',str(root),'due'], env=env, text=True).strip()
        prepared = subprocess.check_output(['python3',helper,'--root',str(root),'prepare','1367549'],env=env,text=True).strip()
        if retain == retry == 'true':
            result = json.loads(prepared)
            assert due == '1367549'
            assert result['ids'] == expected_ids, result['ids']
            assert 86390 < result['next_retry'] - time.time() <= 86400
            print(f'PASS retain={retain} retry={retry}: only {result["ids"]} selected; next retry in 24h')
        else:
            assert not due and not prepared
            assert record.read_bytes() == original
            print(f'PASS retain={retain} retry={retry}: retries paused; pending record unchanged')
assert source.read_bytes() == original_record
for path, digest in checksums.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
print(f'PASS all {len(files)} original audio files and original pending record unchanged')
