from gdo.base.GDO import GDO
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.likes.WithLikes import WithLikes


class GDO_RemixSID(WithLikes, GDO):
    """One HVSC-relative SID path and its successful playback count."""

    def gdo_columns(self):
        return [GDT_AutoInc('sid_id'),
                GDT_String('sid_path').maxlen(512).case_s().not_null().unique(),
                GDT_UInt('sid_plays').not_null().initial('0')]

    def gdo_likes_table(self):
        from gdo.remixes.GDO_RemixSIDLikes import GDO_RemixSIDLikes
        return GDO_RemixSIDLikes.table()

    def gdo_with_dislikes(self):
        return False
