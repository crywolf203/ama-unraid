"""Run the real shell helper in an isolated path tree with a mocked CLI."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'root/scripts/deemix_direct_download.bash'


class DirectHelperTests(unittest.TestCase):
    def run_helper(self, count, retry=None, retain="true", retry_enabled="true"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, downloads = root / 'config', root / 'downloads'
            (config / 'deemix/bambanah').mkdir(parents=True)
            downloads.mkdir()
            script = root / 'helper.bash'
            script.write_text(SCRIPT.read_text().replace('/config', str(config)).replace('/downloads-ama', str(downloads)))
            bindir = root / 'bin'
            bindir.mkdir()
            cli = bindir / 'deemix'
            cli.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
pathlib.Path(os.environ['CALLS']).write_text(json.dumps(args))
out = pathlib.Path(args[args.index('-p') + 1])
for n in range(int(os.environ['COUNT'])):
    (out / f'{n}.mp3').write_bytes(b'test audio')
''')
            cli.chmod(0o755)
            env = dict(os.environ, PATH=f'{bindir}:{os.environ["PATH"]}',
                       COUNT=str(count), CALLS=str(root / 'calls.json'), AMA_EXPECTED_TRACKS='17',
                       RETAIN_PARTIAL_ALBUMS=retain, RETRY_MISSING_TRACKS=retry_enabled,
                       BAMBANAH_CONFIG_HOME=str(config / 'deemix/bambanah'))
            if retain is None:
                env.pop('RETAIN_PARTIAL_ALBUMS', None)
            if retry:
                env['AMA_RETRY_TRACK_IDS_JSON'] = json.dumps(retry)
            result = subprocess.run(['bash', str(script), 'https://www.deezer.com/album/1367549'], env=env,
                                    capture_output=True, text=True, timeout=20)
            calls = json.loads((root / 'calls.json').read_text())
            files = list((downloads / 'temp').glob('*.mp3'))
            return result, calls, len(files)

    def test_partial_audio_is_retained_and_helper_succeeds(self):
        result, _, count = self.run_helper(15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(count, 15)
        self.assertIn('retaining 15 available tracks', result.stdout)

    def test_missing_ids_are_passed_with_original_album_url(self):
        result, calls, count = self.run_helper(1, ['101', '102'])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('--track-ids', calls)
        self.assertEqual(calls[calls.index('--track-ids') + 1], '101,102')
        self.assertEqual(calls[-1], 'https://www.deezer.com/album/1367549')
        self.assertEqual(count, 1)

    def test_default_retention_preserves_old_policy(self):
        result, _, count = self.run_helper(15, retain=None)
        self.assertEqual(result.returncode, 21, result.stdout + result.stderr)
        self.assertEqual(count, 0)

    def test_retention_disabled_restores_rejection(self):
        result, _, count = self.run_helper(15, retain='false')
        self.assertEqual(result.returncode, 21, result.stdout + result.stderr)
        self.assertEqual(count, 0)

    def test_retention_with_retries_paused_keeps_music(self):
        result, _, count = self.run_helper(15, retry_enabled='false')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(count, 15)

    def test_no_downloadable_tracks_still_returns_twenty(self):
        result, _, count = self.run_helper(0)
        self.assertEqual(result.returncode, 20, result.stdout + result.stderr)
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()
