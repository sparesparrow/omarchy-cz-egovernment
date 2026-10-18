import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('egov', ROOT / 'scripts' / 'egov.py')
egov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(egov)


class SkillTests(unittest.TestCase):
    def test_portal_urls_are_official(self):
        self.assertEqual(egov.URLS['obcan'], 'https://obcan.portal.gov.cz/')
        self.assertTrue(all(u.startswith('https://') for u in egov.URLS.values()))

    def test_triage_avoids_deadline_calculation(self):
        result = egov.assess('Okresní soud zaslal výzvu, 12. 10. 2026. Spisová značka: 12 C 1/2026')
        self.assertEqual(result['priorita'], 'VYSOKÁ')
        self.assertIn('12. 10. 2026', result['data_v_textu'])
        self.assertNotIn('datum_konce_lhuty', result)

    def test_bad_endpoint_blocked(self):
        for endpoint in ['http://ws1.datovka.gov.cz/DS/dz',
                         'https://evil.example/DS/dz',
                         'https://ws1.datovka.gov.cz.evil.example/DS/dz',
                         'https://user:pass@ws1.datovka.gov.cz/DS/dz',
                         'https://ws1.datovka.gov.cz/redirect?to=evil']:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                egov.validate_endpoint(endpoint)

    def test_endpoint_official_allowed(self):
        self.assertEqual(egov.validate_endpoint('https://ws1.datovka.gov.cz/DS/dx'),
                         'https://ws1.datovka.gov.cz/DS/dx')

    def test_read_txt_eml(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / 'sample.txt'
            p.write_text('Soudní výzva', encoding='utf-8')
            self.assertIn('Soudní výzva', egov.read_text(p))
            eml = pathlib.Path(td) / 'message.eml'
            eml.write_bytes(b'Subject: Datova schranka\nFrom: notify@example.test\n\nNew alert')
            self.assertIn('New alert', egov.read_text(eml))

    def test_nias_mf_link_is_checked(self):
        from urllib.parse import urlencode
        inner = urlencode({'wa': 'wsignin1.0', 'wtrealm': 'https://isform.mf.gov.cz/be/',
                           'wreply': 'https://isform.mf.gov.cz/be/login/saml2/sso/saml-client'})
        q = urlencode({'wa': 'wsignin1.0', 'wtrealm': 'urn:microsoft:cgg2010:fpsts',
                       'wctx': '?' + inner})
        url = 'https://nia.identita.gov.cz/fpsts/selectrealm?' + q
        self.assertEqual(egov.validate_identity_link(url), url)
        with self.assertRaises(ValueError):
            egov.validate_identity_link(url.replace('nia.identita.gov.cz', 'nia.identita.gov.cz.example'))
        with self.assertRaises(ValueError):
            egov.validate_identity_link(url.replace('isform.mf.gov.cz', 'attacker.example'))

    def test_zfo_requires_user_export(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / 'something.zfo'
            p.write_bytes(b'abcd')
            with self.assertRaisesRegex(ValueError, 'ZFO'):
                egov.read_text(p)


if __name__ == '__main__':
    unittest.main()
