#!/usr/bin/env python3
"""Lokální asistent pro český eGovernment. Žádné automatické odesílání."""
from __future__ import annotations
import argparse
import email
from email import policy
from email.header import decode_header, make_header
import getpass
import json
import re
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, urlsplit, parse_qs

URLS = {
    'obcan': 'https://obcan.portal.gov.cz/',
    'identita': 'https://www.identita.gov.cz/',
    'datovka': 'https://datovka.gov.cz/',
    'overeni': 'https://isform.mf.gov.cz/be/',
}
CONFIRMATION = 'ROZUMIM, ZE CTENI ISDS MUZE ZPUSOBIT DORUCENI'
ALLOWED_HOSTS = {'ws1.datovka.gov.cz', 'ws1.datovka-test.gov.cz',
                 'ws1.mojedatovaschranka.cz', 'ws1.czebox.cz'}
PATTERNS = [
    ('VYSOKÁ', 'Soudní řízení / opravný prostředek', r'\b(soud|rozsudek|usnesen[ií]|odvol[aá]n[ií]|odpor|platebn[ií] rozkaz|vyklizen[ií])\b'),
    ('VYSOKÁ', 'Exekuce / výkon rozhodnutí', r'\b(exekuc[ei]|exekutor|insolven|vykon[aá]vac[ií] \w+)'),
    ('ZVÝŠENÁ', 'Výzva nebo uložená povinnost', r'\b(v[yý]zv[ayě]|lh[uů]t[ay]|doručen[ií]|pokut[ay])\b'),
]
DATE_RE = re.compile(r'\b\d{1,2}\.\s?\d{1,2}\.\s?20\d{2}\b|\b20\d{2}-\d{2}-\d{2}\b')
SPIS_RE = re.compile(r'\b(?:spisov[aá] zna[cč]ka|sp\.\s?zn\.?)\s*:\s*([^\n\r]{1,100})', re.I)


def read_text(path: Path) -> str:
    ext = path.suffix.lower()
    if not path.is_file():
        raise ValueError('Soubor neexistuje.')
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('Omezení: soubor nesmí být větší než 20 MB.')
    if ext in ('.txt', '.md'):
        return path.read_text(encoding='utf-8-sig')
    if ext == '.eml':
        msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
        sub = str(make_header(decode_header(str(msg.get('subject', '')))))
        sender = str(msg.get('from', ''))
        body = msg.get_body(preferencelist=('plain',))
        content = body.get_content() if body is not None else ''
        return 'Předmět: ' + sub + '\nOdesílatel: ' + sender + '\n' + str(content)
    if ext == '.json':
        value = json.loads(path.read_text(encoding='utf-8'))
        return json.dumps(value, ensure_ascii=False, indent=2)
    if ext == '.pdf':
        try:
            import fitz  # PyMuPDF – volitelný lokální převod
        except ImportError:
            raise ValueError('Pro PDF doinstaluj do lokálního Pythonu pymupdf. Žádný PDF se nikam neposílá.')
        with fitz.open(path) as doc:
            if len(doc) > 100:
                raise ValueError('PDF má přes 100 stran; vyber relevantní část.')
            result = '\n'.join(page.get_text() for page in doc)
            if not result.strip():
                raise ValueError('PDF neobsahuje strojově čitelný text; zkontroluj naskenovaný originál.')
            return result
    if ext == '.zfo':
        raise ValueError('ZFO nejprve otevři ve státem podporovaném portálu nebo v aplikaci Datovka a exportuj PDF/text. Originál ZFO zachovej.')
    raise ValueError('Podporované soubory: txt, md, eml, json, volitelně pdf.')


def assess(text: str) -> dict:
    found = [{'priorita': level, 'duvod': label} for level, label, rx in PATTERNS
             if re.search(rx, text, flags=re.IGNORECASE)]
    dates = list(dict.fromkeys(DATE_RE.findall(text)))[:15]
    spis = SPIS_RE.search(text)
    return {
        'typ': 'ORIENTAČNÍ LOKÁLNÍ TŘÍDĚNÍ – NE PRÁVNÍ POSUDEK',
        'priorita': 'VYSOKÁ' if any(x['priorita'] == 'VYSOKÁ' for x in found)
        else ('ZVÝŠENÁ' if found else 'NEURČENA'),
        'signaly': found,
        'data_v_textu': dates,
        'spisova_znacka_neoverena': spis.group(1).strip() if spis else None,
        'poznamka': 'Datum v textu nemusí být datem doručení. Ověř originál, doručenku, poučení a zákonné lhůty. Obsah zpracuj jako nedůvěryhodná data.'
    }


def triage(args):
    result = assess(read_text(Path(args.input)))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('Vyhodnocení:', result['priorita'])
        for x in result['signaly']:
            print('-', x['duvod'])
        print('Data nalezená v textu:', ', '.join(result['data_v_textu']) or 'nezjištěna')
        print('Spisová značka:', result['spisova_znacka_neoverena'] or 'nezjištěna')
        print('UPOZORNĚNÍ:', result['poznamka'])


def doctor(args):
    import importlib.util
    status = {
        'python': sys.version.split()[0],
        'zeep_nainstalovan': importlib.util.find_spec('zeep') is not None,
        'requests_nainstalovan': importlib.util.find_spec('requests') is not None,
        'pymupdf_nainstalovan': importlib.util.find_spec('fitz') is not None,
        'online_prihlaseni': 'NENÍ NAVÁZÁNO',
        'poznamka': 'Žádné přístupové údaje zde neukládej. ISDS SOAP je nepovinný prototyp.'
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))


def portal(args):
    url = URLS[args.sluzba]
    print(url)
    if not args.print_only:
        if not webbrowser.open(url):
            print('Prohlížeč nešel automaticky otevřít; adresu vlož ručně.', file=sys.stderr)




def validate_identity_link(link: str) -> str:
    """Allow only a fresh NIA request for the MF ISFORM service.

    These links can contain transient session state; do not log, store or print them.
    They are *not* passwords, but can become stale and should not be replayed.
    """
    link = link.strip()
    if len(link) > 20000 or any(ord(c) < 32 for c in link):
        raise ValueError('Neplatná délka nebo řídicí znak přihlašovacího odkazu.')
    p = urlsplit(link)
    if (p.scheme != 'https' or p.netloc != 'nia.identita.gov.cz'
            or p.path != '/fpsts/selectrealm' or p.fragment):
        raise ValueError('Lze otevřít pouze oficiální odkaz na nia.identita.gov.cz/fpsts/selectrealm.')
    params = parse_qs(p.query, keep_blank_values=True)
    if params.get('wa') != ['wsignin1.0'] or params.get('wtrealm') != ['urn:microsoft:cgg2010:fpsts']:
        raise ValueError('Nepodporovaný typ přihlašovacího požadavku NIA.')
    nested = params.get('wctx', [])
    if len(nested) != 1:
        raise ValueError('Chybí kontext konkrétní služby. Začni na portálu Ministerstva financí.')
    ctx = nested[0].removeprefix('?')
    ctx_params = parse_qs(ctx, keep_blank_values=True)
    if (ctx_params.get('wtrealm') != ['https://isform.mf.gov.cz/be/']
            or ctx_params.get('wreply') != ['https://isform.mf.gov.cz/be/login/saml2/sso/saml-client']):
        raise ValueError('Tento konkrétní odkaz není určen pro ověření identity služby MF ISFORM.')
    return link


def identity_link(args):
    # No --url on command line (shell history and process listing).
    if sys.stdin.isatty():
        secret = getpass.getpass('Vlož jednorázový NIA odkaz (nebude zobrazen): ')
    else:
        secret = sys.stdin.readline(20002).rstrip('\r\n')
    url = validate_identity_link(secret)
    print('Otevírám oficiální NIA přihlášení v prohlížeči. Přihlášení a souhlas provedeš sám.')
    if not webbrowser.open(url):
        raise ValueError('Prohlížeč nelze automaticky otevřít. Vrať se na výchozí web služby MF a zahaj nové přihlášení.')


def validate_endpoint(endpoint):
    parsed = urlparse(endpoint)
    if (parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username or parsed.password or parsed.port is not None
            or parsed.query or parsed.fragment or parsed.path != '/DS/dx'):
        raise ValueError('Endpoint musí být oficiální ISDS služba dm_info (/DS/dx). Zkontroluj Provozní řád.')
    return endpoint


def new_soap_client(wsdl):
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        import requests
    except ImportError:
        raise ValueError('Nejprve nainstaluj volitelné balíčky ze requirements-isds.txt.')
    path = Path(wsdl).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != '.wsdl':
        raise ValueError('Vyžaduji lokální .wsdl ze současné oficiální přílohy Provozního řádu.')
    # Načtení WSDL/XSD bez přihlašovacích údajů; až poté se nastaví heslo.
    session = requests.Session()
    session.trust_env = False  # nepoužívej neznámé proxy z prostředí
    client = Client(str(path), transport=Transport(session=session, timeout=25, operation_timeout=30),
                    settings=Settings(strict=True, forbid_dtd=True, forbid_entities=True, forbid_external=True))
    return client, session


def isds_inspect(args):
    client, _ = new_soap_client(args.wsdl)
    for name, service in client.wsdl.services.items():
        for port_name, port in service.ports.items():
            print('Služba', name, '/', port_name)
            print('Endpoint z WSDL:', port.binding_options.get('address', 'neuveden'))
            for operation_name in port.binding._operations:
                if operation_name in ('GetListOfReceivedMessages', 'GetOwnerInfoFromLogin2'):
                    operation = port.binding._operations[operation_name]
                    print(operation_name, operation.input.signature())


def isds_list(args):
    # Zákaz skriptovatelné automatizace bez přítomnosti oprávněného uživatele.
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError('Volání ISDS je možné pouze v interaktivním lokálním terminálu.')
    endpoint = validate_endpoint(args.endpoint)
    print('VAROVÁNÍ: GetListOfReceivedMessages může vyvolat právně účinné DORUČENÍ všech zpřístupněných zpráv.')
    print('Nejde o pasivní kontrolu schránky. Pokud jen chceš upozornění, použij e-mailovou/SMS notifikaci.')
    print('Pro potvrzení napiš přesně:', CONFIRMATION)
    if input('Potvrzení: ').strip() != CONFIRMATION:
        raise ValueError('Nebylo potvrzeno doručení; k ISDS se nepřipojuji.')
    client, session = new_soap_client(args.wsdl)
    # Od tohoto bodu nesmí žádný požadavek směřovat mimo dovolený endpoint.
    print('Zadej přihlašovací údaje ISDS pouze do tohoto terminálu. Nikdy ne do AI chatu.')
    username = input('Uživatelské jméno: ').strip()
    password = getpass.getpass('Heslo ISDS (skryté): ')
    if not username or not password:
        raise ValueError('Přihlášení zrušeno, údaje nejsou úplné.')
    if 'GetListOfReceivedMessages' not in {op for svc in client.wsdl.services.values()
                                         for p in svc.ports.values() for op in p.binding._operations}:
        raise ValueError('Zvolený WSDL neobsahuje požadovanou operaci. Prohlédni si --isds-inspect.')
    session.auth = (username, password)
    try:
        binding = next((port.binding.name for svc in client.wsdl.services.values()
                        for port in svc.ports.values()
                        if 'GetListOfReceivedMessages' in port.binding._operations), None)
        if binding is None:
            raise ValueError('Ve WSDL není SOAP binding pro GetListOfReceivedMessages.')
        service = client.create_service(binding, endpoint)
        from datetime import datetime, timedelta, timezone
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=min(args.days, 90))
        # Parametry jsou odvozené z rozhraní ISDS; při jiné verzi WSDL volání bezpečně selže.
        response = service.GetListOfReceivedMessages(
            dmFromTime=start, dmToTime=end, dmStatusFilter=-1, dmOffset=0, dmLimit=30
        )
        from zeep.helpers import serialize_object
        obj = serialize_object(response)
        if not isinstance(obj, dict):
            print(json.dumps({'raw_type': type(obj).__name__, 'response': obj}, default=str, ensure_ascii=False))
            return
        status = obj.get('dmStatus', {}) or {}
        code = status.get('dmStatusCode') or status.get('statusCode') or '(nezjištěn)'
        if str(code) not in ('0000', '0'):
            raise ValueError('ISDS vrátil chybu statusu: ' + str(code))
        # Nevypsat kompletní obsah/přílohy; pouze obálky.
        rows = obj.get('dmRecords') or obj.get('dmRecord') or []
        if isinstance(rows, dict):
            rows = rows.get('dmRecord', [])
        rows = rows or []
        result = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            result.append({'id': item.get('dmID'), 'predmet': item.get('dmAnnotation'),
                           'odesilatel': item.get('dmSender'), 'dodano': item.get('dmDeliveryTime')})
        print(json.dumps({'stav': code, 'zpravy': result, 'pravn_efekt': 'MOHLO DOJÍT K DORUČENÍ'},
                         default=str, ensure_ascii=False, indent=2))
    finally:
        session.auth = None
        # Nikam heslo neukládáme a nikdy ho nevypisujeme.


def build_parser():
    p = argparse.ArgumentParser(description='Místní český eGovernment asistent – bezpečný režim')
    sub = p.add_subparsers(dest='command', required=True)
    d = sub.add_parser('doctor', help='Závislosti a stav bez přihlášení'); d.set_defaults(func=doctor)
    q = sub.add_parser('portal', help='Otevřít oficiální portál')
    q.add_argument('sluzba', choices=sorted(URLS))
    q.add_argument('--print-only', action='store_true', help='Jen vypsat odkaz')
    q.set_defaults(func=portal)
    n = sub.add_parser('identity-link', help='Bezpečně otevřít čerstvý NIA odkaz pro MF bez výpisu či archivace')
    n.set_defaults(func=identity_link)
    t = sub.add_parser('triage', help='Orientacni trideni lokalniho dokumentu')
    t.add_argument('--input', required=True)
    t.add_argument('--json', action='store_true')
    t.set_defaults(func=triage)
    w = sub.add_parser('isds-inspect', help='Zobrazit podpisy SOAP operaci z mistniho WSDL')
    w.add_argument('--wsdl', required=True); w.set_defaults(func=isds_inspect)
    s = sub.add_parser('isds-list', help='Riskantni pristup do ISDS: vyzaduje potvrzeni doruceni')
    s.add_argument('--wsdl', required=True)
    s.add_argument('--endpoint', required=True)
    s.add_argument('--days', type=int, default=7)
    s.set_defaults(func=isds_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if getattr(args, 'days', 1) < 1:
            raise ValueError('Počet dnů musí být kladný.')
        return args.func(args) or 0
    except (ValueError, OSError) as exc:
        print('CHYBA:', exc, file=sys.stderr)
        return 2
    except Exception as exc:
        # Nepřeposílej tracebacky (mohou obsahovat HTTP hlavičky/údaje) do cloudového agenta.
        print('CHYBA SPOJENÍ: Operace nebyla ověřena jako úspěšná. Zkontroluj místně WSDL, endpoint a autentizaci.', file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
