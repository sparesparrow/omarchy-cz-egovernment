#!/usr/bin/env python3
"""Neprivilegovaná instalace jediného skillu pro vybrané AI agenty."""
import argparse
import shutil
from pathlib import Path

TARGETS = {
    'codex': Path.home() / '.agents' / 'skills',
    'openclaw': Path.home() / '.openclaw' / 'skills',
    'hermes': Path.home() / '.hermes' / 'skills',
}


def main():
    p = argparse.ArgumentParser(description='Instalace cz-egovernment do adresářů agentů')
    p.add_argument('--target', choices=['all', *TARGETS], default='all')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--force', action='store_true', help='Přepsat jen stávající adresář cz-egovernment')
    args = p.parse_args()
    source = Path(__file__).resolve().parent.parent
    if not (source / 'SKILL.md').is_file():
        p.error('Nelze najít SKILL.md')
    names = TARGETS if args.target == 'all' else {args.target: TARGETS[args.target]}
    for name, destbase in names.items():
        dest = destbase / 'cz-egovernment'
        if dest.exists() and not args.force:
            print(f'{name}: PŘESKOČENO, složka již existuje: {dest} (--force pro přepsání)')
            continue
        print(f'{name}: {source} -> {dest}' + (' (jen ukázka)' if args.dry_run else ''))
        if args.dry_run:
            continue
        destbase.mkdir(mode=0o700, parents=True, exist_ok=True)
        if dest.exists():
            if dest.is_symlink():
                raise SystemExit('Bezpečnost: instalační cíl je symlink, nelze přepsat: ' + str(dest))
            shutil.rmtree(dest)
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns('.venv', '__pycache__', '*.pyc', '.git'))
    print('Při dalším spuštění agenta bude skill dostupný. Žádná přihlašovací data se nenastavují.')


if __name__ == '__main__':
    main()
