# DrivePass

Los documentos de tu vehículo en tu teléfono: permiso de circulación, SOAP, revisión técnica y padrón, con avisos de vencimiento y Modo control con QR. Sin cuenta, sin nube y cifrados.

- Web: https://diceadev.github.io/drivepass/
- Descargas (APK para Android): [Releases](https://github.com/DiceaDev/drivepass/releases/latest)

Este repositorio solo contiene la página web y los APK publicados. Cada versión incluye su huella SHA-256 para comprobar que el archivo es el original.

DrivePass no es una app oficial y no reemplaza los documentos. Lleva también los físicos si tienes dudas sobre lo que aceptan en un control.

## Datos de descarga

La versión, la fecha, el tamaño, la huella SHA-256 y los enlaces del APK que muestra la web salen de la última release publicada; nadie los escribe a mano.

- `scripts/actualizar-release.py` lee la release desde la API de GitHub, descarga el APK y comprueba que su SHA-256 sea el que informa GitHub y que esté firmado con el certificado de DrivePass (`CERTIFICADO_ESPERADO`). Recién entonces escribe `release.json` y los valores de `index.html` (elementos con `data-release` y enlaces con `data-release-href`), para que se vean también sin JavaScript. Si algo no calza, falla y no cambia nada.
- `.github/workflows/actualizar-release.yml` lo ejecuta al publicarse una release, una vez al día y a mano (*Run workflow*), y guarda los cambios.
- Al cargar, la página vuelve a leer `release.json`, del mismo sitio.

Huella SHA-256 del certificado de firma: `E8:BE:4C:84:8C:6D:46:57:AC:65:57:00:84:27:26:E5:F1:2D:81:3C:7C:26:DA:B7:E0:3F:09:6B:59:3D:48:51` (C=CL, O=DiceaDev, CN=DrivePass). Si algún día cambia la llave de firma, hay que actualizar `CERTIFICADO_ESPERADO` a propósito.

## Privacidad de la web

La página no carga nada de otros sitios: Inter se sirve desde `fuentes/` (licencia SIL OFL en `fuentes/LICENCIA-Inter.txt`), y no hay cookies ni analítica. Una política de seguridad de contenido (CSP) en cada página lo hace cumplir.

- La CSP solo deja ejecutar los scripts cuyo hash aparece en ella. **Después de editar cualquier `<script>`**, ejecuta `python3 scripts/revisar-csp.py --escribir`. El flujo de GitHub Actions falla si la CSP no calza.
- Para saber cuántas veces se descarga cada versión, sin rastrear a nadie: `python3 scripts/descargas.py` (usa el contador público de GitHub).

## Al publicar una versión con funciones nuevas

Los datos de descarga se actualizan solos; el contenido no. Revisa:

1. **Funciones** (`#funciones`), **Documentos** e **Imprevistos**: ¿hay algo nuevo que contar o algo que ya no es así?
2. **Privacidad**: si la función nueva guarda datos, pide un permiso o comparte algo, actualiza la sección de la web y `privacidad.html` (con su fecha de vigencia).
3. **Preguntas frecuentes**: ¿alguna respuesta quedó desactualizada?
4. **Capturas**: si cambió una pantalla que se muestra, tómala en modo demo (patente DEMO, sin datos reales) y reemplázala en `capturas/` con su versión `-360.webp`.
5. **Datos de ejemplo**: fechas, kilómetros y montos de la página deben cuadrar entre sí.
6. Si editaste algún `<script>`: `python3 scripts/revisar-csp.py --escribir`.
