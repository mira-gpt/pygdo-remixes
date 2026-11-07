from gdo.base.Method import Method
from gdo.core.GDT_UInt import GDT_UInt
from gdo.remixes.GDO_RemixSIDLikes import GDO_RemixSIDLikes
from gdo.remixes.method.ipc_sidplay import ROOT, resolve_sid, track_record
from gdo.remixes.sid import select_result


class sidlike(Method):
    def gdo_parameters(self):
        return [GDT_UInt('number').min(1).not_null().positional()]

    def gdo_execute(self):
        try:
            if self._env_session is None or self._env_user is None:
                raise ValueError('An authenticated session is required')
            path, title, _ = select_result(self._env_session, self.param_value('number'))
            relative = resolve_sid(path).relative_to(ROOT.resolve()).as_posix()
            track = track_record(relative)
            GDO_RemixSIDLikes.blank({'like_object': track.get_id(),
                                     'like_user': self._env_user.get_id(),
                                     'like_value': '1'}).soft_replace()
            return self.reply('remixes_sid_liked', (title or relative,))
        except (ValueError, OSError, RuntimeError) as error:
            return self.err('remixes_error', (str(error),))
