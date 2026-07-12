#!/usr/bin/env python3
"""Unifica descarga de Alaric + generación del reporte HTML.

Un solo comando para actualizar todo.

Uso:
    python3 actualizar_reporte.py                 # Descarga mes actual + genera + abre
    python3 actualizar_reporte.py --no-browser    # Sin abrir navegador
    python3 actualizar_reporte.py --all           # Descarga todos los meses históricos
    python3 actualizar_reporte.py YYYY-MM         # Solo un mes específico
    python3 actualizar_reporte.py --serve         # Modo servidor local (tags auto-save)
    python3 actualizar_reporte.py --no-sync       # Saltea sincronización de capturas (rclone)
"""

import json
import os
import subprocess
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any

from src.constants import (
    DOWNLOADER_SCRIPT,
    GENERATOR_SCRIPT,
    OUTPUT_FILE,
    SCRIPT_DIR,
    SYNC_SCREENSHOTS_SCRIPT,
    TAGS_FILE,
    TAGS_SERVER_PORT,
)


class TagServerHandler(SimpleHTTPRequestHandler):
    """Sirve archivos + endpoint /save-tags para guardar tags automáticamente.

    Args:
        *args: Argumentos posicionales para SimpleHTTPRequestHandler.
        **kwargs: Argumentos de palabra clave para SimpleHTTPRequestHandler.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def do_POST(self) -> None:
        """Procesa solicitudes POST para guardar tags."""
        if self.path == "/save-tags":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                tags_data = json.loads(body)
                with open(TAGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(tags_data, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
                print(f"  Tags guardados: {len(tags_data)} trades")
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
                print(f"  Error guardando tags: {e}")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Silencia logs HTTP excepto para POST.

        Args:
            format: Formato del mensaje de log.
            *args: Argumentos para el formato.
        """
        if "POST" in str(args):
            super().log_message(format, *args)


def run_server(port: int = TAGS_SERVER_PORT) -> None:
    """Inicia servidor HTTP local para auto-guardado de tags.

    Args:
        port: Puerto del servidor. Por defecto TAGS_SERVER_PORT.
    """
    print(f"\n  Servidor local: http://localhost:{port}/data/trading_report.html")
    print("  Los tags se guardan automaticamente al pulsar 'Save Tags'.")
    print("  Presiona Ctrl+C para detener el servidor.\n")

    server = HTTPServer(("localhost", port), TagServerHandler)
    try:
        webbrowser.open(f"http://localhost:{port}/data/trading_report.html")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.shutdown()


def sync_screenshots() -> None:
    """Sincroniza capturas desde Google Drive via rclone."""
    print("=" * 60)
    print("Sincronizando capturas de pantalla desde Google Drive...")
    print("=" * 60)
    result = subprocess.run(["bash", SYNC_SCREENSHOTS_SCRIPT], cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print("  [WARN] Fallo sincronizacion de capturas (puede continuar igual)")
    else:
        print("  Capturas sincronizadas OK.")
    print()


def main() -> None:
    """Ejecuta el flujo completo: sincronizar, descargar, generar y abrir."""
    no_browser = "--no-browser" in sys.argv
    serve_mode = "--no-serve" not in sys.argv  # Serve es default
    skip_sync = "--no-sync" in sys.argv
    args = [a for a in sys.argv[1:] if a not in ("--no-browser", "--no-serve", "--serve", "--no-sync")]

    # Paso 0: Sincronizar capturas
    if not skip_sync:
        sync_screenshots()

    # Paso 1: Descargar
    print("=" * 60)
    print("PASO 1/2: Descargando datos de Alaric...")
    print("=" * 60)

    py_cmd = [sys.executable, DOWNLOADER_SCRIPT]
    if args:
        py_cmd.extend(args)

    result = subprocess.run(py_cmd, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print("\n[ERROR] Fallo la descarga. Abortando.")
        sys.exit(1)

    # Paso 2: Generar reporte
    print("\n" + "=" * 60)
    print("PASO 2/2: Generando reporte HTML...")
    print("=" * 60)

    result = subprocess.run([sys.executable, GENERATOR_SCRIPT], cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print("\n[ERROR] Fallo la generacion del reporte.")
        sys.exit(1)

    # Paso 3: Abrir
    if not no_browser and os.path.exists(OUTPUT_FILE):
        if serve_mode:
            print("\n" + "=" * 60)
            print("MODO SERVIDOR: Guardado automatico de tags activado")
            print("=" * 60)
            run_server()
        else:
            url = f"file://{OUTPUT_FILE}"
            print(f"\nAbriendo {url}...")
            print("(Tags se guardan en data/tags.json)")
            webbrowser.open(url)

    print("\nListo. Reporte actualizado.")


if __name__ == "__main__":
    main()
