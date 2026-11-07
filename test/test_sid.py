import tempfile
import asyncio
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from gdo.remixes.sid import metadata, remember_search, search, select_result


class SIDTest(unittest.TestCase):
    def test_playback_rejects_paths_outside_collection(self):
        from gdo.remixes.method.ipc_sidplay import resolve_sid
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'hvsc'
            root.mkdir()
            (root / 'valid.sid').write_bytes(b'PSID')
            outside = Path(directory) / 'outside.sid'
            outside.write_bytes(b'PSID')
            self.assertEqual(root / 'valid.sid', resolve_sid('valid.sid', root))
            with self.assertRaises(ValueError):
                resolve_sid('../outside.sid', root)
            (root / 'link.sid').symlink_to(outside)
            with self.assertRaises(ValueError):
                resolve_sid('link.sid', root)

    def test_search_finds_header_metadata_and_stable_sorted_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = bytearray(118)
            header[:4] = b'PSID'
            header[22:26] = b'Tune'
            header[54:60] = b'Artist'
            (root / 'B.sid').write_bytes(header)
            (root / 'a.sid').write_bytes(header)
            self.assertEqual(('Tune', 'Artist'), metadata(root / 'a.sid'))
            self.assertEqual(['a.sid', 'B.sid'], [row[0] for row in search(root, 'artist')])

    def test_search_snapshot_is_stored_in_session(self):
        class Session(dict):
            def set(self, key, value):
                self[key] = value
        session, other = Session(), Session()
        remember_search(session, 'tune', [('x.sid', 'Tune', 'A')])
        self.assertEqual('tune', session['remixes.sid.search']['query'])
        self.assertEqual('x.sid', select_result(session, 1)[0])
        with self.assertRaises(ValueError):
            select_result(other, 1)
        with self.assertRaises(ValueError):
            select_result(session, 2)


class SIDCommandTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from gdo.base.Application import Application
        from gdo.base.Render import Mode
        Application.mode(Mode.render_cli)

    async def test_search_and_selection_use_same_session(self):
        from gdo.remixes.method.sid import sid
        class Session(dict):
            def set(self, key, value):
                self[key] = value
        session = Session()
        method = sid()
        method._env_session = session
        method.param_value = MagicMock(side_effect=lambda key: {'query': 'tune', 'search': False}[key])
        method.reply = MagicMock()
        with patch('gdo.remixes.method.sid.search', return_value=[('a.sid', 'Tune', 'Artist')]):
            await method.gdo_execute()
        self.assertEqual('tune', session['remixes.sid.search']['query'])
        method.param_value = MagicMock(side_effect=lambda key: {'query': '1', 'search': False, 'subtune': 2}[key])
        db = MagicMock()
        db.is_in_transaction.return_value = False
        with patch('gdo.remixes.method.sid.Application.db', return_value=db), \
                patch('gdo.remixes.method.sid.IPC.send_to_dog') as send, \
                patch('gdo.remixes.method.ipc_sidplay.resolve_sid'), \
                patch('gdo.remixes.method.ipc_sidplay.validate_subtune') as validate:
            await method.gdo_execute()
        send.assert_called_once_with('remixes.ipc_sidplay', ['a.sid', '2'])
        self.assertEqual(2, validate.call_args.args[1])

    def test_subtune_header_bounds(self):
        from gdo.remixes.method.ipc_sidplay import validate_subtune
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'song.sid'
            header = bytearray(16)
            header[:4] = b'PSID'
            header[14:16] = (3).to_bytes(2, 'big')
            path.write_bytes(header)
            validate_subtune(path, 1)
            validate_subtune(path, 3)
            with self.assertRaises(ValueError):
                validate_subtune(path, 0)
            with self.assertRaises(ValueError):
                validate_subtune(path, 4)

    async def test_like_uses_selected_session_track(self):
        from gdo.remixes.method.sidlike import sidlike
        from gdo.remixes.sid import SESSION_KEY
        method = sidlike()
        method._env_session = {SESSION_KEY: {'query': 'tune', 'results': [['a.sid', 'Tune', 'Artist']]}}
        method._env_user = MagicMock(get_id=MagicMock(return_value='9'))
        method.param_value = MagicMock(return_value=1)
        method.reply = MagicMock()
        track = MagicMock(get_id=MagicMock(return_value='7'))
        fakepath = MagicMock()
        fakepath.relative_to.return_value.as_posix.return_value = 'a.sid'
        with patch('gdo.remixes.method.sidlike.resolve_sid', return_value=fakepath), \
                patch('gdo.remixes.method.sidlike.track_record', return_value=track), \
                patch('gdo.remixes.method.sidlike.GDO_RemixSIDLikes.blank') as like:
            method.gdo_execute()
        like.assert_called_once_with({'like_object': '7', 'like_user': '9', 'like_value': '1'})
        like.return_value.soft_replace.assert_called_once()

    async def test_play_counter_only_after_ffmpeg_progress(self):
        from gdo.remixes.method import ipc_sidplay
        class Lines:
            def __init__(self, lines):
                self.lines = iter(lines)
            def __aiter__(self):
                return self
            async def __anext__(self):
                try:
                    return next(self.lines)
                except StopIteration:
                    raise StopAsyncIteration
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'a.sid').write_bytes(b'PSID')
            track = MagicMock()
            decoder = MagicMock(returncode=0, wait=AsyncMock(return_value=0))
            player = MagicMock(returncode=0, wait=AsyncMock(return_value=0))
            player.stdout = Lines([b'out_time_us=0\n', b'out_time_us=500000\n', b'out_time_us=1000000\n'])
            with patch.object(ipc_sidplay, 'ROOT', root), \
                    patch.object(ipc_sidplay, 'resolve_sid', return_value=root / 'a.sid'), \
                    patch.object(ipc_sidplay, 'validate_subtune'), \
                    patch.object(ipc_sidplay, 'track_record', return_value=track), \
                    patch('pathlib.Path.is_file', return_value=True), \
                    patch.object(ipc_sidplay.asyncio, 'create_subprocess_exec', new_callable=AsyncMock, side_effect=[decoder, player]) as spawn:
                await ipc_sidplay.play_sid('a.sid', 'test-sink', 2)
            self.assertIn('-o2', spawn.await_args_list[0].args)
            track.increase.assert_called_once_with('sid_plays')

    async def test_decoder_failure_does_not_count(self):
        from gdo.remixes.method import ipc_sidplay
        class EmptyLines:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            track = MagicMock()
            decoder = MagicMock(returncode=1, wait=AsyncMock(return_value=1))
            player = MagicMock(returncode=0, wait=AsyncMock(return_value=0), stdout=EmptyLines())
            with patch.object(ipc_sidplay, 'ROOT', root), \
                    patch.object(ipc_sidplay, 'resolve_sid', return_value=root / 'a.sid'), \
                    patch.object(ipc_sidplay, 'validate_subtune'), \
                    patch.object(ipc_sidplay, 'track_record', return_value=track), \
                    patch.object(ipc_sidplay.asyncio, 'create_subprocess_exec', new_callable=AsyncMock, side_effect=[decoder, player]):
                with self.assertRaisesRegex(RuntimeError, 'decoding failed'):
                    await ipc_sidplay.play_sid('a.sid', 'test-sink')
            track.increase.assert_not_called()

    async def test_failed_audio_output_does_not_count(self):
        from gdo.remixes.method import ipc_sidplay
        class EmptyLines:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            track = MagicMock()
            decoder = MagicMock(returncode=0, wait=AsyncMock(return_value=0))
            player = MagicMock(returncode=1, wait=AsyncMock(return_value=1), stdout=EmptyLines())
            with patch.object(ipc_sidplay, 'ROOT', root), \
                    patch.object(ipc_sidplay, 'resolve_sid', return_value=root / 'a.sid'), \
                    patch.object(ipc_sidplay, 'validate_subtune'), \
                    patch.object(ipc_sidplay, 'track_record', return_value=track), \
                    patch('pathlib.Path.is_file', return_value=True), \
                    patch.object(ipc_sidplay.asyncio, 'create_subprocess_exec', new_callable=AsyncMock, side_effect=[decoder, player]):
                with self.assertRaisesRegex(RuntimeError, 'playback failed'):
                    await ipc_sidplay.play_sid('a.sid', 'test-sink')
            track.increase.assert_not_called()

    async def test_cancellation_terminates_both_pipeline_processes(self):
        from gdo.remixes.method import ipc_sidplay
        reading = asyncio.Event()
        class BlockingLines:
            def __aiter__(self):
                return self
            async def __anext__(self):
                reading.set()
                await asyncio.Event().wait()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decoder = MagicMock(returncode=None)
            async def wait_decoder():
                if decoder.returncode is None:
                    await asyncio.Event().wait()
                return decoder.returncode
            decoder.wait = AsyncMock(side_effect=wait_decoder)
            decoder.terminate.side_effect = lambda: setattr(decoder, 'returncode', -15)
            player = MagicMock(returncode=None, wait=AsyncMock(return_value=-15), stdout=BlockingLines())
            player.terminate.side_effect = lambda: setattr(player, 'returncode', -15)
            with patch.object(ipc_sidplay, 'ROOT', root), \
                    patch.object(ipc_sidplay, 'resolve_sid', return_value=root / 'a.sid'), \
                    patch.object(ipc_sidplay, 'validate_subtune'), \
                    patch.object(ipc_sidplay, 'track_record', return_value=MagicMock()), \
                    patch.object(ipc_sidplay.asyncio, 'create_subprocess_exec', new_callable=AsyncMock, side_effect=[decoder, player]):
                task = asyncio.create_task(ipc_sidplay.play_sid('a.sid', 'test-sink'))
                await reading.wait()
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            decoder.terminate.assert_called_once()
            player.terminate.assert_called_once()
