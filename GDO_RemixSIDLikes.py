from gdo.likes.GDO_LikeTable import GDO_LikeTable


class GDO_RemixSIDLikes(GDO_LikeTable):
    def gdo_liked_table(self):
        from gdo.remixes.GDO_RemixSID import GDO_RemixSID
        return GDO_RemixSID.table()
