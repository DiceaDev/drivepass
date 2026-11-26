#!/usr/bin/env python3
"""Cuenta las descargas de cada APK publicado, sin cookies ni analítica.

Usa el contador público que GitHub lleva por archivo (download_count). Cuenta descargas
del archivo, no personas: una misma persona que descarga dos veces suma dos.

Uso: python3 scripts/descargas.py   (con GITHUB_TOKEN opcional para evitar el límite de consultas)
"""
import json
import os
import urllib.request


def releases():
    pagina, todas = 1, []
    while True:
        peticion = urllib.request.Request(
            f'https://api.github.com/repos/DiceaDev/drivepass/releases?per_page=100&page={pagina}',
            headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'drivepass-web'},
        )
        if os.environ.get('GITHUB_TOKEN'):
            peticion.add_header('Authorization', f'Bearer {os.environ["GITHUB_TOKEN"]}')
        with urllib.request.urlopen(peticion, timeout=30) as r:
            lote = json.load(r)
        if not lote:
            return todas
        todas += lote
        pagina += 1


def main():
    total = 0
    print(f'{"Versión":<10} {"Publicada":<12} {"Descargas":>9}')
    for rel in releases():
        n = sum(a['download_count'] for a in rel['assets'] if a['name'].lower().endswith('.apk'))
        total += n
        print(f'{rel["tag_name"]:<10} {rel["published_at"][:10]:<12} {n:>9}')
    print(f'{"Total":<23} {total:>9}')


if __name__ == '__main__':
    main()
