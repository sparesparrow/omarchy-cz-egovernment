# Přístupy, doručování, zdroje (ověřeno 18. října 2026)

**Oficiální zdroje**

- Přístup aplikací přes SOAP/WSDL: https://datovka.gov.cz/info/cs/74.html – aplikační rozhraní může používat oprávněný uživatel bez předchozí registrace.
- Aktuální provozní řád a technické přílohy: https://datovka.gov.cz/info/cs/80.html
- Pro vývojáře a změny: https://datovka.gov.cz/info/cs/2052.html
- Přihlášení aplikací třetích stran Mobilním klíčem: https://datovka.gov.cz/info/cs/help/15.3.text.html. Uživatel si může v nastavení vygenerovat údaje pro externí aplikaci; žádný generovaný kód neukládat do skillu ani neposílat do chatu. Pro skutečné zavedení této metody je třeba samostatně implementovat autorizovaný protokol podle příloh provozního řádu.
- Doručování: https://portalobcana.gov.cz/cs/napoveda/clanky-a-navody/doruceni-datovych-zprav
- Rizika přeposílání datových zpráv: https://obcan.gov.cz/cs/napoveda/clanky-a-navody/nastaveni-portalu-obcana
- Změna přihlašování do Portálu občana od 1. 8. 2026: https://obcan.gov.cz/cs/napoveda/clanky-a-navody/zmena-prihlasovani
- Identita občana: https://info.identita.gov.cz/Portal/Default.aspx

## Podstatné odlišení

- **Upozornění na novou zprávu** nemusí znamenat, že celá datová zpráva byla stažena nebo přečtena; neplést s přeposláním kompletní datové zprávy do e-mailu. Účinky konkrétního nastavení ověř na oficiálním portálu.
- **Přihlášení/operace pro příjem** mohou mít právní účinky. Ověřit `dmDeliveryTime`, `dmAcceptanceTime`, údaje doručenky a poučení. Nepředpokládat automaticky datum konce lhůty.
- **eIdentita NIA** je autentizace identity; nelze ji obecně ztotožnit s programovým přístupem do Portálu občana. Žádné získávání nebo recyklace session cookie z portálu.
- **Zabezpečení:** přístupové údaje do ISDS musí zůstat na zařízení ovládaném uživatelem. Agent v cloudu má pracovat raději s vybranými exporty. Uživatel sám potvrzuje MFA.
- **Archivy:** lokální export není ověřená archivace ani náhrada právně významného ZFO; uchovávat originální zprávu a doručenku v originálním formátu. Konzultovat možnosti Datového trezoru / Datovky.

## Stav prototypu

Lokální třídění funguje offline. Integrace přes SOAP klienta je závislá na dokumentaci WSDL dané verze a oprávněních; produkční spojení nebylo v rámci tohoto balíčku provedené, protože by vyžadovalo přihlašovací údaje uživatele a mohlo vyvolat doručení. Příklad endpointu se před skutečným voláním musí ověřit.
