#!/usr/bin/env python3
"""Escribe en la web los datos de la última versión publicada de DrivePass.

Lee la última release de DiceaDev/drivepass desde la API de GitHub y actualiza:
  - release.json: lo que index.html lee al cargar.
  - index.html: los valores escritos en la página (elementos con data-release y
    enlaces con data-release-href), para que se vean también sin JavaScript.

Antes de escribir nada descarga el APK y comprueba dos cosas:
  - que su SHA-256 sea el que GitHub informa del archivo subido (campo "digest");
  - que esté firmado con el certificado de DrivePass (CERTIFICADO_ESPERADO, esquemas de firma v2/v3).
Si algo no calza o no tiene el formato esperado, termina con error y no toca nada.

Uso: GITHUB_TOKEN=... python3 scripts/actualizar-release.py
"""
import hashlib
import json
import os
import struct
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = 'DiceaDev/drivepass'
RAIZ = Path(__file__).resolve().parent.parent
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic']
URL_APK = re.compile(r'^https://github\.com/DiceaDev/drivepass/releases/download/v\d+\.\d+\.\d+/[\w.-]+\.apk$')
# Huella SHA-256 del certificado con que se firma DrivePass (C=CL, O=DiceaDev, CN=DrivePass).
# Si alguna vez cambia la llave de firma, hay que actualizarla aquí a propósito.
CERTIFICADO_ESPERADO = 'e8be4c848c6d4657ac655700842726e5f12d813c7c26dab7e03f096b593d4851'
URL_NOTAS = re.compile(r'^https://github\.com/DiceaDev/drivepass/releases/tag/v\d+\.\d+\.\d+$')


def ultima_release():
    peticion = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/releases/latest',
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'drivepass-web'},
    )
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        peticion.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(peticion, timeout=30) as r:
        return json.load(r)


def descargar(url):
    peticion = urllib.request.Request(url, headers={'User-Agent': 'drivepass-web'})
    with urllib.request.urlopen(peticion, timeout=300) as r:
        return r.read()


def certificados_firma(apk):
    """Huellas SHA-256 del primer certificado de cada esquema de firma v2/v3 del APK."""
    eocd = apk.rfind(b'PK\x05\x06')
    if eocd < 0:
        sys.exit('El archivo no parece un APK')
    inicio_cd = struct.unpack('<I', apk[eocd + 16:eocd + 20])[0]
    if apk[inicio_cd - 16:inicio_cd] != b'APK Sig Block 42':
        sys.exit('El APK no tiene bloque de firma v2/v3')
    tam = struct.unpack('<Q', apk[inicio_cd - 24:inicio_cd - 16])[0]
    pos, fin, pares = inicio_cd - tam, inicio_cd - 24, {}
    while pos < fin:
        largo = struct.unpack('<Q', apk[pos:pos + 8])[0]
        pares[struct.unpack('<I', apk[pos + 8:pos + 12])[0]] = apk[pos + 12:pos + 8 + largo]
        pos += 8 + largo

    def con_largo(b, o):
        n = struct.unpack('<I', b[o:o + 4])[0]
        return b[o + 4:o + 4 + n], o + 4 + n

    huellas = {}
    for nombre, ident in (('v2', 0x7109871A), ('v3', 0xF05368C0)):
        if ident in pares:
            firmantes, _ = con_largo(pares[ident], 0)
            firmante, _ = con_largo(firmantes, 0)
            firmado, _ = con_largo(firmante, 0)
            _, o = con_largo(firmado, 0)
            certificados, _ = con_largo(firmado, o)
            certificado, _ = con_largo(certificados, 0)
            huellas[nombre] = hashlib.sha256(certificado).hexdigest()
    if not huellas:
        sys.exit('No se encontró firma v2 ni v3')
    return huellas


def verificar_apk(d):
    apk = descargar(d['apk'])
    if len(apk) != d['bytes']:
        sys.exit('El tamaño descargado no coincide con el informado por GitHub')
    if hashlib.sha256(apk).hexdigest() != d['sha256']:
        sys.exit('El SHA-256 del APK descargado no coincide con el que informa GitHub')
    huellas = certificados_firma(apk)
    if set(huellas.values()) != {CERTIFICADO_ESPERADO}:
        sys.exit(f'El APK no está firmado con el certificado de DrivePass: {huellas}')


def datos(rel):
    version = str(rel.get('tag_name', '')).removeprefix('v')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        sys.exit(f'Versión inesperada: {rel.get("tag_name")!r}')
    apks = [a for a in rel.get('assets', []) if str(a.get('name', '')).lower().endswith('.apk')]
    if len(apks) != 1:
        sys.exit(f'Se esperaba un APK en la release y hay {len(apks)}')
    apk = apks[0]
    huella = re.fullmatch(r'sha256:([0-9a-f]{64})', apk.get('digest') or '')
    if not huella:
        sys.exit('El APK no trae la huella SHA-256 (digest) de GitHub')
    if not URL_APK.match(apk.get('browser_download_url', '')) or not URL_NOTAS.match(rel.get('html_url', '')):
        sys.exit('Enlaces fuera del repositorio esperado')
    if not isinstance(apk.get('size'), int) or apk['size'] <= 0:
        sys.exit('Tamaño del APK inválido')
    publicada = datetime.fromisoformat(rel['published_at'].replace('Z', '+00:00'))
    return {
        'version': version,
        'publicada': rel['published_at'],
        'bytes': apk['size'],
        'sha256': huella.group(1),
        'apk': apk['browser_download_url'],
        'notas': rel['html_url'],
        'certificado': CERTIFICADO_ESPERADO,
        '_fecha': publicada.astimezone(ZoneInfo('America/Santiago')),
    }


def escribir_html(html, d):
    f = d['_fecha']
    textos = {
        'version': d['version'],
        'placa': 'V' + '·'.join(d['version'].split('.')),
        'fecha': f'{f.day} {MESES[f.month - 1]} {f.year}',
        'tamano': f'{round(d["bytes"] / 1048576)} MB',
        'huella': d['sha256'],
        'certificado': ':'.join(CERTIFICADO_ESPERADO[i:i + 2] for i in range(0, 64, 2)).upper(),
    }
    for clave, texto in textos.items():
        patron = re.compile(r'(<(\w+)\b[^>]*\bdata-release="' + clave + r'"[^>]*>)[^<]*(</\2>)')
        html, n = patron.subn(lambda m: m.group(1) + texto + m.group(3), html)
        if n == 0:
            sys.exit(f'index.html no tiene elementos data-release="{clave}"')
    for clave in ('apk', 'notas'):
        etiqueta = re.compile(r'<a\b[^>]*\bdata-release-href="' + clave + r'"[^>]*>')
        html, n = etiqueta.subn(lambda m: re.sub(r'(?<![\w-])href="[^"]*"', f'href="{d[clave]}"', m.group(0)), html)
        if n == 0:
            sys.exit(f'index.html no tiene enlaces data-release-href="{clave}"')
    return html


def main():
    d = datos(ultima_release())
    verificar_apk(d)
    publico = {k: v for k, v in d.items() if not k.startswith('_')}
    (RAIZ / 'release.json').write_text(json.dumps(publico, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ruta = RAIZ / 'index.html'
    ruta.write_text(escribir_html(ruta.read_text(encoding='utf-8'), d), encoding='utf-8')
    print(f'Versión {d["version"]} · {publico["bytes"]} bytes · sha256 {d["sha256"]}')


if __name__ == '__main__':
    main()
