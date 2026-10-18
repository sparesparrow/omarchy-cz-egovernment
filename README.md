# Omarchy CZ eGovernment

Native **Omarchy/Quickshell bar widget** plus an optional Czech **Agent Skill** for Codex, OpenClaw, and Hermes. No credentials or citizen records are stored in this repository.

> **Status:** prototype v0.2.0. The QML widget was checked statically but **not run on a live Omarchy desktop**. The optional SOAP/ISDS client is experimental and is not connected automatically.

## What you get

- A native icon in the Omarchy bar. **Left click** opens [Portál občana](https://obcan.portal.gov.cz/); **middle click** opens [Datové schránky](https://datovka.gov.cz/); **right click** opens [Elektronicky ověřit identitu](https://isform.mf.gov.cz/be/) at the Ministry of Finance ISFORM service (NIA login).
- Each link opens in your regular browser via `xdg-open`. **You sign in personally**, including any BankID, Mobile Key or MFA challenge.
- An optional local `cz-egovernment` skill can classify exported `.txt`, `.md`, `.eml`, `.json`, or text-based `.pdf` documents; it does not submit anything. Experimental direct SOAP is separately gated, local and *never invoked by the QML widget*.
- **No polling, unattended logins or message sending.** Simply opening the login page does not read a Data Box message; **actual successful login or certain ISDS operations can have legal delivery effects**.

## Install the Omarchy plugin (Omarchy Quattro / supported shell)

Once this repository is public on GitHub:

```bash
omarchy plugin add https://github.com/sparesparrow/omarchy-cz-egovernment.git
omarchy plugin validate ~/.config/omarchy/plugins/sparesparrow.egovernment
omarchy plugin enable sparesparrow.egovernment
omarchy plugin list
```

Omarchy may offer to enable during installation. Only run `enable` if it is not yet enabled. Plugins execute user-level code in the shell; **review before enabling**. Without Omarchy Quattro's plugin interface, the native widget is not compatible. Do not run this on older Omarchy releases and assume it worked.

Removal:

```bash
omarchy plugin remove sparesparrow.egovernment
```

## Elektronicky ověřit identitu / NIA (Ministry of Finance)

The supplied NIA URL is a **session-specific WS-Federation sign-in request** (`nia.identita.gov.cz/fpsts/selectrealm`) to the Ministry of Finance's `https://isform.mf.gov.cz/be/` application. Do **not** save this multi-kilobyte link in source, shell history, a bookmark, or logs: it includes transient `wctx` and relay-state values and can expire. Open the origin service (`https://isform.mf.gov.cz/be/`) and start a **new authentication session** in your own browser. If you already hold a fresh NIA URL locally, the optional skill supports:

```bash
python3 agents/cz-egovernment/scripts/egov.py identity-link
```

Paste your link at its **hidden local prompt**; the command validates the official NIA host, the exact login endpoint and the expected MF ISFORM return target, then opens it without printing the URL. Actual verification, identity-method choice, consent and 2FA remain entirely in the browser under your control. The program **does not** capture/reuse a SAML token or sign in on your behalf. The origin service could require navigating to a specific electronic form; the `/be/` home page is not guaranteed to start the same flow automatically.

## Optional AI skill (no Omarchy privileges)

From the cloned repository:

```bash
python3 agents/cz-egovernment/scripts/install.py --target all --dry-run
python3 agents/cz-egovernment/scripts/install.py --target all
python3 agents/cz-egovernment/scripts/egov.py doctor
python3 -m unittest discover -s agents/cz-egovernment/tests -v
```

Targets: **Codex** `~/.agents/skills/cz-egovernment`, **OpenClaw** `~/.openclaw/skills/cz-egovernment`, **Hermes** `~/.hermes/skills/cz-egovernment`. If you use custom state directories or a nonstandard Hermes profile, adapt the target manually. This installer never uses `sudo`, never touches the Data Box and refuses to overwrite an installed skill unless `--force` is supplied.

More details and legal safeguards: [SKILL.md](agents/cz-egovernment/SKILL.md), [safety notes](agents/cz-egovernment/references/bezpecnost-a-doruceni.md).

## Publishing to GitHub

The repository should be called `sparesparrow/omarchy-cz-egovernment`. To publish directly from your own Omarchy machine (after `gh auth login`), run the interactive helper:

```bash
bash scripts/publish.sh
```

It checks that your signed-in GitHub account is `sparesparrow` and asks you to confirm the repository will be public. Alternatively, create an **empty public repository** in the [GitHub web interface](https://github.com/new?name=omarchy-cz-egovernment) and push the files manually.

Do not choose "Add README" or "Add .gitignore" when creating an empty repository using the web form. The project already includes both. Only source code and a fictional example belong on GitHub — **never commit actual Datová schránka messages, identity documents, passwords, tokens, WSDL credentials or PDFs.**

## Verification

Offline:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s agents/cz-egovernment/tests -v
```

Live compatibility check **on an Omarchy Quattro machine**:

```bash
omarchy plugin validate ./
omarchy plugin list
```

## Sources

- [Omarchy Shell Plugins manual](https://omarchy.org/manual/shell-plugins/)
- [Omarchy Quattro shell reference](https://github.com/omacom/omarchy/blob/quattro/docs/omarchy-shell.md)
- [Official Citizen Portal](https://obcan.portal.gov.cz/)
- [Official Data Box portal](https://datovka.gov.cz/)
- [Official Identity of Citizen](https://www.identita.gov.cz/)

MIT licensed. This is a third-party plugin, **not affiliated with the Czech government or Omarchy**.
