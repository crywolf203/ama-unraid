"""Exercise real ProcessArtist finalization and retry gates with isolated media."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).parents[1] / 'root/scripts'


class ArtistPipelineTests(unittest.TestCase):
    def test_partial_finalizes_then_missing_track_merges_and_completes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, downloads, staged = root / 'config', root / 'downloads', root / 'staged'
            for folder in (config / 'scripts', config / 'ignore', config / 'list',
                           config / 'cache/artists/5080', downloads, staged):
                folder.mkdir(parents=True, exist_ok=True)
            (config / 'cache/artists/5080/5080-info.json').write_text('{"nb_fan":100}')
            tracks = [{'id':str(n), 'title':f'Track {n}', 'artist':'Artist', 'disc':1, 'track':n} for n in (1,2,3)]
            catalog_file = root / 'catalog.json'
            catalog_file.write_text(json.dumps(tracks))
            helper = (SCRIPTS / 'partial_albums.py').read_text()
            helper = helper.replace("Path('/config/partial-albums')", repr(config / 'partial-albums').replace('PosixPath', 'Path'))
            helper = helper.replace("if __name__ == '__main__':", f"catalog = lambda _: json.loads(Path({str(catalog_file)!r}).read_text())\nif __name__ == '__main__':")
            (config / 'scripts/partial_albums.py').write_text(helper)
            for n in (1,2,3):
                subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','anullsrc', '-t','0.1',
                                '-metadata',f'title=Track {n}', '-metadata',f'track={n}/3',
                                '-metadata','disc=1/1',str(staged / f'{n}.mp3')], check=True)
            source = (SCRIPTS / 'download.bash').read_text()
            a = source.index('ProcessArtist () {')
            b = source.index('\nAlbumFilter ()', a)
            function = source[a:b].replace('/config',str(config)).replace('/downloads-ama',str(downloads)).replace('/tmp/deemix-imgs',str(root / 'images'))
            album = {'id':1367549,'title':'Test','artist':{'id':5080,'name':'Artist'},
                     'release_date':'2020-01-01','record_type':'album','explicit_lyrics':False,'nb_tracks':3,'cover_xl':''}
            prelude = f'''export RETAIN_PARTIAL_ALBUMS=true
export RETRY_MISSING_TRACKS=true
albumlistdata='{json.dumps([album])}'
artistid=5080
albumids=(1367549)
albumcount=1
ALBUM_FILTER=false
FAN_COUNT=0
IGNORE_ARTIST_WITHOUT_IMAGE=false
FOLDERPERM=755
FILEPERM=644
logheaderstart=TEST
logheader=TEST
log() {{ echo "$*"; }}
DownloadQualityCheck() {{ :; }}
Conversion() {{ return 0; }}
AddReplaygainTags() {{ :; }}
PlexNotification() {{ :; }}
ArtistInfo() {{ :; }}
ffmpeg() {{ return 1; }}
curl() {{ return 0; }}
chown() {{ return 0; }}
DownloadAlbumWithClient() {{
  mkdir -p '{downloads}/temp'
  if [ "${{AMA_PARTIAL_RETRY:-false}}" = true ]; then
    cp '{staged}/3.mp3' '{downloads}/temp/'
  else
    cp '{staged}/1.mp3' '{staged}/2.mp3' '{downloads}/temp/'
  fi
}}
'''
            script = root / 'run.bash'
            script.write_text(prelude + function + '\nProcessArtist\n')
            result = subprocess.run(['bash', str(script)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            queue = config / 'partial-albums/1367549.json'
            self.assertTrue(queue.exists(), result.stdout + result.stderr)
            state = json.loads(queue.read_text())
            self.assertEqual([t['id'] for t in state['missing']], ['3'])
            target = Path(state['target'])
            original_hash = hashlib.sha256((target/'1.mp3').read_bytes()).hexdigest()
            self.assertFalse((config/'logs/downloads/1367549').exists())
            # Normal scans must not redownload this pending partial album.
            result = subprocess.run(['bash',str(script)],capture_output=True,text=True,timeout=30)
            self.assertIn('queued for scheduled',result.stdout)
            # A reserved retry processes the original folder and only staged track 3.
            script.write_text(prelude + f'export AMA_PARTIAL_RETRY=true\nexport AMA_PARTIAL_TARGET="{target}"\n' + function + '\nProcessArtist\n')
            result = subprocess.run(['bash',str(script)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout + result.stderr)
            self.assertEqual(len(list(target.glob('*.mp3'))),3)
            self.assertEqual(hashlib.sha256((target/'1.mp3').read_bytes()).hexdigest(), original_hash)
            self.assertFalse(queue.exists(), result.stdout + result.stderr)
            self.assertTrue((config/'logs/downloads/1367549').exists())


if __name__ == '__main__':
    unittest.main()
