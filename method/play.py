import asyncio
from urllib.error import URLError

import msgspec.json

from gdo.base.Application import Application
from gdo.base.IPC import IPC
from gdo.base.Method import Method
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.remixes.kwed import search


class play(Method):
    @classmethod
    def gdo_trig(cls):
        return 'kwed.play'

    def gdo_user_permission(self):
        return 'owner'

    def gdo_locks_session(self):
        return False

    def gdo_parameters(self):
        return [GDT_RestOfText('search').not_null().tooltip('tt_remixes_search')]

    async def gdo_execute(self):
        try:
            title, url = await asyncio.to_thread(search, self.param_value('search'))
            if len(msgspec.json.encode([url])) > IPC.MAX_EVENT_ARG_SIZE:
                raise ValueError('Track URL exceeds IPC size limit')
            args = ('remixes.ipc_play', [url])
            if Application.db().is_in_transaction():
                Application.defer_after_commit(IPC.send_to_dog, *args)
            else:
                IPC.send_to_dog(*args)
            return self.reply('remixes_play_queued', (title, url))
        except (ValueError, OSError, URLError, RuntimeError) as exc:
            return self.err('remixes_error', (str(exc),))
