#!/usr/bin/env python3
"""Mantiene al día la política de seguridad de contenido (CSP) de las páginas.

La CSP solo deja ejecutar los scripts de la página cuyo hash SHA-256 aparece en ella. Si se edita
un <script>, su hash cambia y el navegador lo bloquea. Este script:
  - sin argumentos: revisa que la CSP de cada página tenga exactamente los hashes de sus scripts
    (termina con error si no; lo usa el flujo de GitHub Actions);
  - con --escribir: recalcula los hashes y los escribe en la CSP.

Uso: python3 scripts/revisar-csp.py [--escribir]
"""
import base64
import hashlib
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = ['index.html', 'privacidad.html']
# Los <script type="application/ld+json"> son datos, no se ejecutan: la CSP no los afecta.
SCRIPT = re.compile(r'<script(?![^>]*type="application/ld\+json")[^>]*>(.*?)</script>', re.S)
CSP = re.compile(r'(<meta http-equiv="Content-Security-Policy" content=")([^"]*)(">)')


def politica(hashes):
    script = ' '.join(f"'{h}'" for h in hashes) if hashes else "'none'"
    return ("default-src 'none'; "
            f"script-src {script}; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self'; font-src 'self'; connect-src 'self'; "
            "base-uri 'none'; form-action 'none'")


def main():
    escribir = '--escribir' in sys.argv
    errores = []
    for nombre in PAGINAS:
        ruta = RAIZ / nombre
        html = ruta.read_text(encoding='utf-8')
        hashes = ['sha256-' + base64.b64encode(hashlib.sha256(s.encode('utf-8')).digest()).decode()
                  for s in SCRIPT.findall(html)]
        esperada = politica(hashes)
        actual = CSP.search(html)
        if not actual:
            errores.append(f'{nombre}: no tiene CSP')
            continue
        if actual.group(2) == esperada:
            print(f'{nombre}: CSP al día ({len(hashes)} script(s))')
        elif escribir:
            ruta.write_text(CSP.sub(lambda m: m.group(1) + esperada + m.group(3), html, count=1), encoding='utf-8')
            print(f'{nombre}: CSP actualizada ({len(hashes)} script(s))')
        else:
            errores.append(f'{nombre}: la CSP no coincide con los scripts. Ejecuta: python3 scripts/revisar-csp.py --escribir')
    if errores:
        sys.exit('\n'.join(errores))


if __name__ == '__main__':
    main()
