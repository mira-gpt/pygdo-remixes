import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.remixes.module_remixes import module_remixes
from gdotest.TestUtil import cli_plug, reinstall_module, cli_gizmore, GDOTestCase, WebPlug, install_module, web_plug


class module_remixes_Test(GDOTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        install_module('remixes')
        loader.load_modules_db(True)
        WebPlug.COOKIES = {}
        Application.init_cli()
        loader.init_modules(True, True)
        loader.init_cli()

    def test_00_reinstall(self):
        reinstall_module('remixes')
        self.assertIs(type(module_remixes.instance()), module_remixes, "Cannot re-install module remixes.")

    def test_03_overview_cli(self):
        giz =  cli_gizmore()
        out = cli_plug(giz, "$remixes.overview")
        self.assertIsNotNone(out, '$remixes.overview does not work.')

    def test_02_overview_web(self):
        giz =  cli_gizmore()
        out = web_plug("remixes.overview.html")
        self.assertIsNotNone(out, 'remixes.overview.html does not work.')


if __name__ == '__main__':
    unittest.main()
