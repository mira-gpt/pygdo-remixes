import asyncio
from pathlib import Path

import msgspec.json

from gdo.base.Application import Application
from gdo.base.IPC import IPC
from gdo.base.Method import Method
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDT_UInt import GDT_UInt
from gdo.remixes.sid import remember_search, search, select_result


class sid(Method):
    def gdo_user_permission(self):
        return 'owner'

    def gdo_parameters(self):
        return [GDT_RestOfText('query').not_null(), GDT_Bool('search'),
                GDT_UInt('subtune').min(1).max(65535).initial('1')]

    async def gdo_execute(self):
        try:
            session = self._env_session
            if session is None or not hasattr(session, 'get') or not hasattr(session, 'set'):
                raise ValueError('A session is required for SID search')
            query = self.param_value('query').strip()
            if not query or len(query) > 200:
                raise ValueError('SID search must contain 1 to 200 characters')
            if query.isdecimal() and not self.param_value('search'):
                path, title, author = select_result(session, int(query))
                subtune = self.param_value('subtune')
                from gdo.remixes.method.ipc_sidplay import resolve_sid, validate_subtune
                validate_subtune(resolve_sid(path), subtune)
                args = ('remixes.ipc_sidplay', [path, str(subtune)])
                if len(msgspec.json.encode(args[1])) > IPC.MAX_EVENT_ARG_SIZE:
                    raise ValueError('SID path exceeds IPC limit')
                if Application.db().is_in_transaction():
                    Application.defer_after_commit(IPC.send_to_dog, *args)
                else:
                    IPC.send_to_dog(*args)
                return self.reply('remixes_sid_queued', (title or Path(path).stem,))
            root = Path(__file__).resolve().parent.parent / 'hvsc'
            results = await asyncio.to_thread(search, root, query, 25)
            remember_search(session, query, results)
            if not results:
                return self.reply('remixes_sid_empty', (query,))
            listing = ' | '.join(f'{index}. {title or Path(path).stem} ({author or "?"})'
                                 for index, (path, title, author) in enumerate(results, 1))
            return self.reply('remixes_sid_results', (listing,))
        except (ValueError, OSError, RuntimeError) as error:
            return self.err('remixes_error', (str(error),))
