import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PluginTests(unittest.TestCase):
    def test_manifest(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['schemaVersion'], 1)
        self.assertEqual(manifest['id'], 'sparesparrow.egovernment')
        self.assertNotIn('omarchy.', manifest['id'])
        self.assertEqual(manifest['kinds'], ['bar-widget'])
        self.assertTrue((ROOT / manifest['entryPoints']['barWidget']).is_file())
        self.assertFalse(any(p.is_symlink() for p in ROOT.rglob('*')))

    def test_widget_is_a_launcher_only(self):
        qml = (ROOT / 'Egovernment.qml').read_text(encoding='utf-8')
        for url in ('https://obcan.portal.gov.cz/', 'https://datovka.gov.cz/',
                    'https://isform.mf.gov.cz/be/'):
            self.assertIn(url, qml)
        self.assertIn('Quickshell.execDetached(["xdg-open", url])', qml)
        self.assertIn('onPressed:', qml)
        for forbidden in ('curl ', 'password', 'session.auth', 'GetListOfReceivedMessages'):
            self.assertNotIn(forbidden, qml)

    def test_skill_present(self):
        self.assertTrue((ROOT / 'agents' / 'cz-egovernment' / 'SKILL.md').is_file())


if __name__ == '__main__':
    unittest.main()
