"""Decode and play one selected HVSC SID in the Dog process."""
import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from gdo.audio.module_audio import module_audio
from gdo.audio.PlaybackTasks import PlaybackTasks
from gdo.base.Application import Application
from gdo.base.Exceptions import GDODBException
from gdo.base.Logger import Logger
from gdo.base.Method import Method
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.remixes.GDO_RemixSID import GDO_RemixSID

TASKS = set()
ROOT = Path(__file__).resolve().parent.parent / 'hvsc'


def resolve_sid(relative, root=ROOT):
    root = root.resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    path.relative_to(root)
    if path.suffix.lower() != '.sid' or not path.is_file():
        raise ValueError('Not an HVSC SID file')
    return path


def track_record(relative):
    table = GDO_RemixSID.table()
    track = table.get_by_vals({'sid_path': relative})
    if track:
        return track
    try:
        return GDO_RemixSID.blank({'sid_path': relative, 'sid_plays': '0'}).insert()
    except GDODBException:
        # A concurrent request may have inserted the same unique path.
        track = table.get_by_vals({'sid_path': relative})
        if not track:
            raise
        return track


def validate_subtune(path, subtune):
    with path.open('rb') as source:
        header = source.read(16)
    if len(header) < 16 or header[:4] not in (b'PSID', b'RSID'):
        raise ValueError('Invalid SID header')
    songs = int.from_bytes(header[14:16], 'big')
    if not 1 <= subtune <= songs:
        raise ValueError(f'Subtune must be between 1 and {songs}')


async def play_sid(relative, output, subtune=1):
    if not output:
        raise ValueError('Audio output device is not configured')
    path = resolve_sid(relative)
    validate_subtune(path, subtune)
    track = track_record(path.relative_to(ROOT.resolve()).as_posix())
    with TemporaryDirectory(prefix='pygdo-sid-') as directory:
        wav = Path(directory) / 'sid.wav'
        os.mkfifo(wav, 0o600)
        decoder = player = monitor = None
        try:
            decoder = await asyncio.create_subprocess_exec(
                'sidplayfp', '-q', '-t180', f'-o{subtune}', f'-w{wav}', str(path),
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            player = await asyncio.create_subprocess_exec(
                'ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-re',
                '-i', str(wav), '-vn', '-progress', 'pipe:1', '-nostats',
                '-f', 'pulse', '-device', output, 'pygdo-sid',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            async def watch_decoder():
                if await decoder.wait() and player.returncode is None:
                    try:
                        player.terminate()
                    except ProcessLookupError:
                        pass
            monitor = asyncio.create_task(watch_decoder())
            counted = False
            async for raw in player.stdout:
                line = raw.decode('ascii', errors='ignore').strip()
                if not counted and line.startswith('out_time_us='):
                    try:
                        progressed = int(line.partition('=')[2]) > 0
                    except ValueError:
                        progressed = False
                    if progressed:
                        track.increase('sid_plays')
                        counted = True
            if await player.wait():
                raise RuntimeError('SID playback failed')
            if await decoder.wait():
                raise RuntimeError('SID decoding failed')
            if not counted:
                raise RuntimeError('SID playback did not produce audio')
        finally:
            if monitor is not None and not monitor.done():
                monitor.cancel()
            for process in (player, decoder):
                if process is not None and process.returncode is None:
                    try:
                        process.terminate()
                    except ProcessLookupError:
                        pass
            for process in (player, decoder):
                if process is not None:
                    await process.wait()
            if monitor is not None:
                await asyncio.gather(monitor, return_exceptions=True)


async def run_sid(relative, subtune=1):
    try:
        await play_sid(relative, module_audio.instance().cfg_output_device(), subtune)
    except (ValueError, OSError, RuntimeError, GDODBException) as error:
        Logger.warning(f'SID playback failed: {error}')


class ipc_sidplay(Method):
    @classmethod
    def gdo_trigger(cls):
        return ''

    def gdo_parameters(self):
        return [GDT_String('path').maxlen(512).not_null().positional(),
                GDT_UInt('subtune').min(1).max(65535).not_null().positional()]

    def gdo_execute(self):
        if Application.IS_DOG:
            task = PlaybackTasks.start(run_sid(self.param_val('path'), self.param_value('subtune')))
            TASKS.add(task)
            task.add_done_callback(TASKS.discard)
        return self.empty()
