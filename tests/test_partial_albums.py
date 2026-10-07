import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).parents[1] / 'root/scripts/partial_albums.py'
spec = importlib.util.spec_from_file_location('partial_albums', MODULE)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)


def track(number, disc=1, title=None):
    return {'id': str(number + disc * 100), 'title': title or f'Track {number}',
            'artist': 'Artist', 'isrc': '', 'disc': disc, 'track': number}


def tags(number, disc=1, title=None):
    return {'title': title or f'Track {number}', 'track': f'{number}/17', 'disc': f'{disc}/2'}


class PartialAlbumTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(pa.os.environ, {'RETAIN_PARTIAL_ALBUMS': 'true', 'RETRY_MISSING_TRACKS': 'true'})
        environment.start()
        self.addCleanup(environment.stop)

    def test_only_two_missing_of_seventeen_are_selected(self):
        expected = [track(n) for n in range(1, 18)]
        actual = [Path(str(n)) for n in range(1, 16)]
        missing = pa.missing_tracks(expected, actual, lambda p: tags(int(p.name)))
        self.assertEqual([t['track'] for t in missing], [16, 17])

    def test_duplicate_titles_match_disc_and_position(self):
        expected = [track(1, 1, 'Same'), track(1, 2, 'Same')]
        missing = pa.missing_tracks(expected, [Path('one')], lambda _: tags(1, 2, 'Same'))
        self.assertEqual(missing, [expected[0]])

    def test_file_count_does_not_hide_wrong_tracks(self):
        missing = pa.missing_tracks([track(1), track(2)], [Path('a'), Path('b')], lambda _: tags(1))
        self.assertEqual(missing, [track(2)])

    def test_bad_or_untagged_audio_remains_missing(self):
        self.assertEqual(pa.missing_tracks([track(1)], [Path('a')], lambda _: {}), [track(1)])

    def test_complete_record_clears_queue_and_marks_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'partial-albums'
            state = {'album_id': '1367549', 'complete': False}
            pa.finish(root, state)
            self.assertTrue((root / '1367549.json').exists())
            state['complete'] = True
            pa.finish(root, state)
            self.assertFalse((root / '1367549.json').exists())
            self.assertTrue((root.parent / 'logs/downloads/1367549').exists())

    def test_partial_record_removes_stale_complete_marker_without_touching_music(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'partial-albums'
            marker = root.parent / 'logs/downloads/1367549'
            marker.parent.mkdir(parents=True)
            marker.touch()
            music = root.parent / 'keep.mp3'
            music.write_bytes(b'audio')
            pa.finish(root, {'album_id': '1367549', 'complete': False})
            self.assertFalse(marker.exists())
            self.assertEqual(music.read_bytes(), b'audio')

    def test_metadata_outage_still_records_partial_album(self):
        state = {'album_id': '1', 'target': '/nonexistent', 'expected': 17}
        def unavailable(_):
            raise OSError('offline')
        pa.refresh(state, unavailable)
        self.assertFalse(state['complete'])
        self.assertEqual(state['catalog_error'], 'offline')

    def test_prepare_reserves_retry_and_returns_only_missing_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'partial-albums'
            album = Path(directory) / 'music'
            album.mkdir()
            (album / 'one.mp3').write_bytes(b'audio')
            state = {'album_id': '1', 'target': str(album), 'expected': 2,
                     'tracks': [track(1), track(2)], 'next_retry': 0}
            pa.write_json(root / '1.json', state)
            import io
            out = io.StringIO()
            with patch('sys.argv', ['partial_albums.py', '--root', str(root), 'prepare', '1']), patch.object(pa, 'probe', return_value=tags(1)), patch('sys.stdout', out):
                pa.main()
            result = json.loads(out.getvalue())
            self.assertEqual(result['ids'], [track(2)['id']])
            self.assertGreater(result['next_retry'], 0)
            out = io.StringIO()
            with patch('sys.argv', ['partial_albums.py', '--root', str(root), 'prepare', '1']), patch('sys.stdout', out):
                pa.main()
            self.assertEqual(out.getvalue(), '')

    def test_pausing_either_flag_does_not_change_queue_or_music(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'partial-albums'
            queue = root / '1.json'
            pa.write_json(queue, {'album_id': '1', 'next_retry': 0})
            original = queue.read_bytes()
            for settings in ({'RETRY_MISSING_TRACKS': 'false'}, {'RETAIN_PARTIAL_ALBUMS': 'false'}):
                for command in ('due', 'prepare'):
                    argv = ['partial_albums.py', '--root', str(root), command]
                    if command == 'prepare':
                        argv.append('1')
                    with patch.dict(pa.os.environ, settings), patch('sys.argv', argv):
                        pa.main()
                    self.assertEqual(queue.read_bytes(), original)

    def test_record_is_created_when_retention_enabled_but_retries_paused(self):
        import io
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'partial-albums'
            music = Path(directory) / 'music'; music.mkdir()
            (music / 'one.mp3').write_bytes(b'audio')
            argv = ['partial_albums.py', '--root', str(root), 'record', '1', str(music), '2', '7']
            with patch.dict(pa.os.environ, {'RETRY_MISSING_TRACKS': 'false'}), patch('sys.argv', argv), patch('sys.stdin', io.StringIO('{"id":1}')), patch.object(pa, 'catalog', return_value=[track(1),track(2)]), patch.object(pa, 'probe', return_value=tags(1)), patch('sys.stdout', io.StringIO()):
                pa.main()
            record = json.loads((root / '1.json').read_text())
            self.assertEqual([t['id'] for t in record['missing']], [track(2)['id']])
            self.assertFalse((root.parent / 'logs/downloads/1').exists())

    def test_interval_setting_and_legacy_alias(self):
        with patch.dict(pa.os.environ, {'PARTIAL_RETRY_HOURS': '6'}):
            self.assertEqual(pa.retry_interval(), 21600)
        with patch.dict(pa.os.environ, {'AMA_PARTIAL_RETRY_HOURS': '3'}):
            with patch.dict(pa.os.environ):
                pa.os.environ.pop('PARTIAL_RETRY_HOURS', None)
                self.assertEqual(pa.retry_interval(), 10800)
        with patch.dict(pa.os.environ, {'PARTIAL_RETRY_HOURS': '0'}):
            self.assertEqual(pa.retry_interval(), 86400)

    def test_successful_later_retry_clears_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            album = Path(directory) / 'music'
            album.mkdir()
            for n in (1, 2):
                (album / f'{n}.mp3').write_bytes(b'audio')
            state = {'album_id': '1', 'target': str(album), 'expected': 2, 'tracks': [track(1), track(2)]}
            with patch.object(pa, 'probe', side_effect=lambda p: tags(int(p.stem))):
                pa.refresh(state)
            self.assertTrue(state['complete'])
            self.assertEqual(state['missing'], [])


if __name__ == '__main__':
    unittest.main()
