#!/usr/bin/env python3
"""Persist partial albums and reserve retries of only their missing Deezer tracks."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.request

AUDIO = {'.flac', '.mp3', '.m4a', '.opus', '.ogg', '.aac'}


def fetch(url):
    if not url.startswith('https://api.deezer.com/'):
        raise ValueError('Unexpected Deezer metadata URL')
    with urllib.request.urlopen(url, timeout=20) as response:
        data = json.load(response)
    if data.get('error'):
        raise ValueError(str(data['error']))
    return data


def catalog(album_id):
    url = f'https://api.deezer.com/album/{album_id}/tracks?limit=100'
    result, pages = [], set()
    while url:
        if url in pages:
            raise ValueError('Repeated catalog page')
        pages.add(url)
        data = fetch(url)
        for item in data['data']:
            # Public album track lists may omit disc/track positions.
            detail = fetch(f"https://api.deezer.com/track/{item['id']}")
            result.append({
                'id': str(item['id']), 'title': detail['title'],
                'artist': detail['artist']['name'], 'isrc': detail.get('isrc', ''),
                'disc': int(detail.get('disk_number') or 1),
                'track': int(detail.get('track_position') or 0),
            })
        url = data.get('next')
    return result


def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).casefold().split())


def number(value):
    try:
        return int(str(value).split('/')[0])
    except (ValueError, TypeError):
        return 0


def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_format',
                             '-of', 'json', str(path)], capture_output=True,
                            text=True, timeout=30, check=True)
    data = json.loads(result.stdout)['format']
    if float(data.get('duration', 0)) <= 0:
        raise ValueError('Audio has no duration')
    return {k.lower(): v for k, v in data.get('tags', {}).items()}


def missing_tracks(tracks, files, reader=None):
    reader = reader or probe
    remaining = list(tracks)
    for path in sorted(files):
        try:
            tags = reader(path)
        except (ValueError, KeyError, subprocess.SubprocessError):
            continue
        disc = number(tags.get('disc', tags.get('discnumber', '1'))) or 1
        position = number(tags.get('track', tags.get('tracknumber', '0')))
        for index, track in enumerate(remaining):
            # Match the original album slot and title, never merely a file count.
            if (normalize(tags.get('title', '')) == normalize(track['title']) and
                position == track['track'] and disc == track['disc'] and position > 0):
                remaining.pop(index)
                break
    return remaining


def audio_files(folder):
    return [p for p in Path(folder).rglob('*')
            if p.is_file() and p.suffix.lower() in AUDIO and p.stat().st_size > 0]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
        json.dump(data, stream, indent=2)
        temporary = stream.name
    os.replace(temporary, path)


def refresh(state, get_catalog=None):
    get_catalog = get_catalog or catalog
    if not state.get('tracks'):
        try:
            state['tracks'] = get_catalog(state['album_id'])
            state.pop('catalog_error', None)
        except Exception as error:
            state['catalog_error'] = str(error)
    files = audio_files(state['target'])
    state['audio_count'] = len(files)
    state['missing'] = missing_tracks(state.get('tracks', []), files)
    state['complete'] = (len(state.get('tracks', [])) == state['expected'] and
                         state['expected'] > 0 and not state['missing'])
    return state


def finish(root, state):
    path = root / f"{state['album_id']}.json"
    complete = root.parent / 'logs' / 'downloads' / state['album_id']
    if state['complete']:
        complete.parent.mkdir(parents=True, exist_ok=True)
        complete.touch()
        path.unlink(missing_ok=True)
    else:
        complete.unlink(missing_ok=True)
        write_json(path, state)


def enabled(name, default):
    return os.environ.get(name, default) == 'true'


def retry_interval():
    raw = os.environ.get('PARTIAL_RETRY_HOURS', os.environ.get('AMA_PARTIAL_RETRY_HOURS', '24'))
    try:
        hours = int(raw)
        if hours < 1:
            raise ValueError()
    except ValueError:
        print('PARTIAL_ALBUM :: Invalid retry interval; using 24 hours', file=sys.stderr)
        hours = 24
    return hours * 3600


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/config/partial-albums'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('due')
    prepare = sub.add_parser('prepare')
    prepare.add_argument('album_id', type=int)
    record = sub.add_parser('record')
    record.add_argument('album_id', type=int)
    record.add_argument('target')
    record.add_argument('expected', type=int)
    record.add_argument('artist_id', type=int)
    args = parser.parse_args()
    if not enabled('RETAIN_PARTIAL_ALBUMS', 'false'):
        return
    if args.command != 'record' and not enabled('RETRY_MISSING_TRACKS', 'true'):
        return
    args.root.mkdir(parents=True, exist_ok=True)
    interval = retry_interval()
    with (args.root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        now = time.time()
        if args.command == 'due':
            for path in sorted(args.root.glob('*.json')):
                try:
                    state = json.loads(path.read_text())
                    if state.get('next_retry', 0) <= now:
                        print(state['album_id'])
                except (ValueError, KeyError):
                    continue
            return
        path = args.root / f'{args.album_id}.json'
        state = json.loads(path.read_text()) if path.exists() else {}
        if args.command == 'record':
            album = json.load(sys.stdin)
            state.update(album_id=str(args.album_id), target=args.target,
                         expected=args.expected, artist_id=args.artist_id, album=album)
            state.setdefault('next_retry', now + interval)
            refresh(state)
            finish(args.root, state)
            print(f"PARTIAL_ALBUM :: {args.album_id}: {len(state['missing'])} missing; "
                  f"complete={state['complete']}; audio={state['audio_count']}")
        else:
            if not state or state.get('next_retry', 0) > now:
                return
            if not Path(state['target']).is_dir():
                state['next_retry'] = now + interval
                state['catalog_error'] = 'Album folder missing; retry deferred'
                write_json(path, state)
                return
            refresh(state)
            state['next_retry'] = now + interval
            finish(args.root, state)
            if not state['complete'] and state.get('missing'):
                print(json.dumps({**state, 'ids': [t['id'] for t in state['missing']]}))


if __name__ == '__main__':
    main()
