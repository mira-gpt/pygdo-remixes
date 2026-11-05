import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import URLError

from gdo.audio.module_audio import module_audio
from gdo.audio.playback import play_file
from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Method import Method
from gdo.core.GDT_String import GDT_String
from gdo.remixes.kwed import download

TASKS = set()


async def play_track(url: str, output: str):
    try:
        if not output:
            raise ValueError('Audio output device is not configured')
        with TemporaryDirectory(prefix='pygdo-remix-') as directory:
            path = Path(directory) / 'track.mp3'
            await asyncio.to_thread(download, url, path)
            await play_file(path, output)
    except (ValueError, OSError, URLError, RuntimeError) as exc:
        Logger.warning(f'Kwed playback failed: {exc}')


class ipc_play(Method):
    @classmethod
    def gdo_trigger(cls):
        return ''

    def gdo_parameters(self):
        return [GDT_String('url').not_null().maxlen(768).positional()]

    def gdo_execute(self):
        if Application.IS_DOG:
            task = asyncio.create_task(play_track(self.param_val('url'), module_audio.instance().cfg_output_device()))
            TASKS.add(task)
            task.add_done_callback(TASKS.discard)
        return self.empty()
