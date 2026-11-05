import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.base.Application import Application
from gdo.base.Render import Mode
from gdo.remixes.kwed import Results, kwed_url, search
from gdo.remixes.method.play import play


class KwedTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Application.mode(Mode.render_cli)

    def test_extract_first_track_and_reject_external_url(self):
        parser = Results()
        parser.feed('<a class="download" href="/download.php/123/Artist%20-%20Song.mp3">Song &amp; More</a>'
                    '<a class="download" href="/download.php/456/Other.mp3">Other</a>')
        self.assertEqual('Song & More', ''.join(parser.title))
        self.assertEqual('https://remix.kwed.org/download.php/123/Artist%20-%20Song.mp3', parser.url)
        with self.assertRaises(ValueError):
            kwed_url('https://evil.example/download.php/1/test.mp3')

    def test_no_results(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'<html>No results</html>'
        with patch('gdo.remixes.kwed.build_opener') as opener:
            opener.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, 'No matching'):
                search('not a track')

    async def test_command_queues_first_result(self):
        method = play()
        self.assertEqual('kwed.play', method.gdo_trig())
        method.param_value = MagicMock(return_value='last v8')
        method.reply = MagicMock(return_value='queued')
        db = MagicMock()
        db.is_in_transaction.return_value = False
        url = 'https://remix.kwed.org/download.php/123/song.mp3'
        with patch.object(Application, 'db', return_value=db), \
                patch('gdo.remixes.method.play.search', return_value=('Song', url)), \
                patch('gdo.remixes.method.play.IPC.send_to_dog') as send:
            self.assertEqual('queued', await method.gdo_execute())
        send.assert_called_once_with('remixes.ipc_play', [url])
        method.reply.assert_called_once_with('remixes_play_queued', ('Song', url))

    async def test_track_is_played_and_temp_file_removed(self):
        from gdo.remixes.method.ipc_play import play_track
        paths = []
        def fake_download(url, path):
            paths.append(path)
            path.write_bytes(b'audio')
        with patch('gdo.remixes.method.ipc_play.download', side_effect=fake_download), \
                patch('gdo.remixes.method.ipc_play.play_file', new_callable=AsyncMock) as player:
            await play_track('https://remix.kwed.org/download.php/123/song.mp3', 'mira_effects')
        player.assert_awaited_once_with(paths[0], 'mira_effects')
        self.assertFalse(paths[0].exists())
