#!/usr/bin/env python3
"""Descarga reportes de Alaric Securities desde PropReports.

Genera CSVs mensuales en Reports_Alaric/ compatibles con generate_report.py.

Uso:
  python3 download_alaric.py [YYYY-MM]  # Un mes especifico
  python3 download_alaric.py --all       # Todos los meses desde 2025
  python3 download_alaric.py --year 2025 # Todo un ano
"""

import contextlib
import os
import sys
import time
from calendar import monthrange
from datetime import datetime

import requests
import xlrd

from constants import (
    ALARIC_DIR,
    ALARIC_TARGET_HEADERS,
    DEFAULT_HISTORICAL_YEARS,
    DIAS_SEMANA,
    ENV_FILE_PERMISSIONS,
    ENV_PATH,
    FMT_MDY,
    FMT_MDY_HMS,
    GASTOS_DIR,
    MESES_ES,
    PROPREPORTS_BASE_URL,
    PROPREPORTS_LOGIN_BACKOFF,
    PROPREPORTS_LOGIN_RETRIES,
    PROPREPORTS_TIMEOUT,
    PROPREPORTS_TIMEOUT_AJUSTES,
)


# Cargar .env si existe
def _load_env() -> None:
    """Carga variables de entorno desde .env si existe."""
    if os.path.exists(ENV_PATH):
        with contextlib.suppress(OSError):
            os.chmod(ENV_PATH, ENV_FILE_PERMISSIONS)
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


_load_env()

USER = os.environ.get("PROPREPORTS_USER")
PASSWORD = os.environ.get("PROPREPORTS_PASSWORD")
GROUP_ID = os.environ.get("PROPREPORTS_GROUP_ID")
ACCOUNT_ID = os.environ.get("PROPREPORTS_ACCOUNT_ID")

# Validación temprana: fallar alto si faltan credenciales
_MISSING = [
    k
    for k, v in [
        ("PROPREPORTS_USER", USER),
        ("PROPREPORTS_PASSWORD", PASSWORD),
        ("PROPREPORTS_GROUP_ID", GROUP_ID),
        ("PROPREPORTS_ACCOUNT_ID", ACCOUNT_ID),
    ]
    if not v
]
if _MISSING:
    print(f"[ERROR] Variables de entorno faltantes: {', '.join(_MISSING)}")
    print("  Ejecuta 'python3 src/setup.py' para configurar o crea un .env manualmente.")
    sys.exit(1)
OUTPUT_DIR = ALARIC_DIR

session = requests.Session()


def login() -> bool:
    """Autentica en PropReports.

    Realiza hasta PROPREPORTS_LOGIN_RETRIES intentos de login con
    backoff configurable entre reintentos.

    Returns:
        True si el login fue exitoso, False en caso contrario.
    """
    print(f"Conectando a {PROPREPORTS_BASE_URL}...")
    for intento in range(1, PROPREPORTS_LOGIN_RETRIES + 1):
        try:
            r = session.post(
                f"{PROPREPORTS_BASE_URL}/login.php?forward=report.php&isEmbedded=0",
                data={"user": USER, "password": PASSWORD},
                timeout=PROPREPORTS_TIMEOUT,
            )
            if "Sign Out" in r.text:
                print("Login exitoso")
                return True
            if intento < PROPREPORTS_LOGIN_RETRIES:
                print(f"  Intento {intento} fallido, reintentando...")
                time.sleep(PROPREPORTS_LOGIN_BACKOFF[intento - 1])
        except requests.RequestException as e:
            print(f"  Error conexion (intento {intento}): {e}")
            if intento < PROPREPORTS_LOGIN_RETRIES:
                time.sleep(PROPREPORTS_LOGIN_BACKOFF[intento - 1])
    print("Login fallido tras 3 intentos")
    return False


def fix_xls_bom(data: bytes) -> bytes:
    """Corrige el BOM de archivos XLS exportados por PropReports.

    PropReports exporta XLS con un byte-swapped BOM (0xFF 0xFE en
    posiciones 28-29 en lugar de 0xFE 0xFF). Esta funcion lo revierte
    para que xlrd pueda leerlo correctamente.

    Args:
        data: Contenido binario del archivo XLS.

    Returns:
        Datos con el BOM corregido.
    """
    data = bytearray(data)
    if len(data) > 30 and data[28] == 0xFF and data[29] == 0xFE:
        data[28] = 0xFE
        data[29] = 0xFF
    return bytes(data)


def download_month(year: int, month: int) -> str | None:
    """Descarga trades de un mes desde PropReports y genera CSV.

    Args:
        year: Ano (ej. 2025).
        month: Mes (1-12).

    Returns:
        Ruta al CSV generado, o None si no hay datos.
    """
    last_day = monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-{last_day:02d}"

    print(f"  {year}-{month:02d}: {start} -> {end}")

    url = (
        f"{PROPREPORTS_BASE_URL}/report.php"
        f"?startDate={start}&endDate={end}"
        f"&groupId={GROUP_ID}&accountId={ACCOUNT_ID}"
        f"&reportName=trades&mode=1&baseCurrency=USD&export=1"
    )

    r = session.get(url)
    if r.status_code != 200 or len(r.content) < 1000:
        print(f"    Sin datos ({len(r.content)} bytes)")
        return None

    xls_data = fix_xls_bom(r.content)
    tmp_path = f"/tmp/alaric_{year}{month:02d}.xls"
    with open(tmp_path, "wb") as f:
        f.write(xls_data)

    wb = xlrd.open_workbook(tmp_path)
    sheet = wb.sheet_by_index(0)

    if sheet.nrows < 3:
        os.remove(tmp_path)
        return None

    # Mapa de columnas del XLS -> posicion
    xls_headers = [str(sheet.cell_value(1, c)).strip() for c in range(sheet.ncols)]
    col_idx = {h: i for i, h in enumerate(xls_headers)}

    def get_xls(row_idx: int, names: str | list[str], default: str = "") -> str:
        """Obtiene el valor de una celda del XLS por nombre(s) de columna.

        Args:
            row_idx: Indice de fila en la hoja.
            names: Nombre(s) de columna a buscar.
            default: Valor por defecto si no se encuentra.

        Returns:
            Valor de la celda como string.
        """
        for name in names if isinstance(names, list) else [names]:
            if name in col_idx:
                val = sheet.cell_value(row_idx, col_idx[name])
                cell_type = sheet.cell_type(row_idx, col_idx[name])
                if cell_type == xlrd.XL_CELL_DATE:
                    try:
                        dt = xlrd.xldate_as_datetime(val, wb.datemode)
                        return dt.strftime("%m/%d/%Y %H:%M:%S")
                    except Exception:
                        return str(val)
                return str(val).strip()
        return default

    csv_filename = f"Alaric Securities  - {MESES_ES[month]}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows_written = 0
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(ALARIC_TARGET_HEADERS) + "\n")

        for r in range(2, sheet.nrows):
            symbol = get_xls(r, ["Symbol"])
            # Saltar filas de agrupacion y headers repetidos
            if not symbol or symbol in ("Equities", "Options", "Futures", "Forex", "Symbol"):
                continue
            opened = get_xls(r, "Opened")
            # Saltar si Opened no es una fecha (es un header repetido)
            if not opened or "/" not in opened or opened.startswith("Opened"):
                continue
            closed = get_xls(r, "Closed")
            held = get_xls(r, "Held")

            # Calcular Weekday
            weekday = ""
            if opened:
                try:
                    for fmt in FMT_MDY_HMS:
                        try:
                            dt = datetime.strptime(opened, fmt)
                            weekday = DIAS_SEMANA[dt.weekday()]
                            break
                        except ValueError:
                            continue
                except (ValueError, IndexError):
                    pass

            tipo = get_xls(r, "Type")
            entry = get_xls(r, "Entry")
            exit_px = get_xls(r, "Exit")
            qty = get_xls(r, "Qty")
            gross = get_xls(r, "Gross")
            comm = get_xls(r, "Comm")
            ecn_fee = get_xls(r, "ECN Fee")
            sec = get_xls(r, "SEC")
            clr = get_xls(r, "CLR")
            nscc = get_xls(r, "NSCC")
            nfa = get_xls(r, "NFA")
            orf = get_xls(r, "ORF")
            misc = get_xls(r, "MISC")
            net_val = get_xls(r, "Net")

            # SECTAF = SEC + TAF (Transaction Activity Fee)
            taf = get_xls(r, "TAF")
            try:
                sectaf = float(sec) + float(taf) if sec or taf else ""
            except ValueError:
                sectaf = ""

            # CL = CLR + NFA + ORF + MISC + CAT
            cat = get_xls(r, "CAT")
            try:
                cl = sum(
                    float(x) for x in [clr, nfa, orf, misc, cat] if x and x.replace(".", "").replace("-", "").isdigit()
                )
            except Exception:
                cl = ""

            # TTC = total fees aproximado
            try:
                # Normalize number string before float conversion
                fees = []
                for x in (comm, ecn_fee, sec, clr, nscc, taf, nfa, orf, misc):
                    if not x:
                        continue
                    cleaned = x.replace(",", "").replace("-", "").strip()
                    if cleaned.replace(".", "").isdigit():
                        fees.append(abs(float(cleaned)))
                ttc = sum(fees)
            except Exception:
                ttc = ""

            row = [
                opened,  # Opened
                closed,  # Closed
                held,  # Held
                USER,  # Account
                symbol,  # Symbol
                tipo,  # Type
                "USD",  # CCY
                entry,  # Entry
                exit_px,  # Exit
                qty,  # Qty
                gross,  # Gross
                comm,  # Comm
                ecn_fee,  # Ecn Fee
                str(sectaf),  # SECTAF
                nscc,  # NSCC
                str(cl),  # CL
                str(ttc),  # TTC
                net_val,  # ATNET (After-Trade Net)
                "",  # TAG
                weekday,  # Weekday
            ]

            f.write(",".join(row) + "\n")
            rows_written += 1

    os.remove(tmp_path)
    size_kb = os.path.getsize(csv_path) / 1024
    print(f"    {rows_written} trades -> {csv_filename} ({size_kb:.1f} KB)")
    return csv_path


def download_ajustes(year: int, month: int) -> str | None:
    """Descarga ajustes de un mes desde PropReports y genera CSV.

    Args:
        year: Ano (ej. 2025).
        month: Mes (1-12).

    Returns:
        Ruta al CSV generado, o None si no hay datos.
    """
    last_day = monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-{last_day:02d}"

    print(f"  Ajustes {year}-{month:02d}: {start} -> {end}")

    url = (
        f"{PROPREPORTS_BASE_URL}/report.php"
        f"?reportName=adjustment&groupId={GROUP_ID}&accountId={ACCOUNT_ID}"
        f"&dateRange=custom&startDate={start}&endDate={end}&export=1"
    )

    r = session.get(url, timeout=PROPREPORTS_TIMEOUT_AJUSTES)
    if r.status_code != 200 or len(r.content) < 1000:
        print(f"    Sin ajustes ({len(r.content)} bytes)")
        return None

    xls_data = fix_xls_bom(r.content)
    tmp_path = f"/tmp/alaric_ajustes_{year}{month:02d}.xls"
    with open(tmp_path, "wb") as f:
        f.write(xls_data)

    wb = xlrd.open_workbook(tmp_path)
    sheet = wb.sheet_by_index(0)

    if sheet.nrows < 3:
        os.remove(tmp_path)
        print("    Sin ajustes")
        return None

    csv_filename = f"Alaric Securities  - Gastos-{MESES_ES[month].capitalize()}.csv"
    csv_path = os.path.join(GASTOS_DIR, csv_filename)
    os.makedirs(GASTOS_DIR, exist_ok=True)

    rows_written = 0
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Date,Category,Comment,Debit\n")
        for r in range(1, sheet.nrows):
            date_val = sheet.cell_value(r, 0)
            category = str(sheet.cell_value(r, 1)).strip() if sheet.ncols > 1 else ""
            comment = str(sheet.cell_value(r, 2)).strip() if sheet.ncols > 2 else ""
            debit = str(sheet.cell_value(r, 3)).strip() if sheet.ncols > 3 else ""

            if not category or category in ("Category", "Date"):
                continue
            if "Total" in category or "Net" in category:
                continue

            # Convert date if it's a float (xlrd serial date)
            if isinstance(date_val, float) and date_val > 0:
                try:
                    dt = xlrd.xldate_as_datetime(date_val, wb.datemode)
                    date_str = dt.strftime(FMT_MDY[0])
                except Exception:
                    date_str = str(date_val)
            else:
                date_str = str(date_val).strip()

            if not date_str or "/" not in date_str:
                continue

            f.write(f"{date_str},{category},{comment},{debit}\n")
            rows_written += 1

    os.remove(tmp_path)
    if rows_written > 0:
        print(f"    {rows_written} ajustes -> {csv_filename}")
    return csv_path


def main() -> None:
    """Punto de entrada: interpreta argumentos y orquesta descargas."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not login():
        sys.exit(1)

    months: list[tuple[int, int]] = []
    now = datetime.now()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--all":
            for y in DEFAULT_HISTORICAL_YEARS:
                for m in range(1, 13):
                    if y == 2026 and m > now.month:
                        break
                    months.append((y, m))
        elif arg == "--year":
            year = int(sys.argv[2])
            months = [(year, m) for m in range(1, 13) if not (year == 2026 and m > now.month)]
        elif "-" in arg and len(arg) == 7:
            y, m = arg.split("-")
            months = [(int(y), int(m))]
        else:
            print("Uso: download_alaric.py [YYYY-MM | --year YYYY | --all]")
            sys.exit(1)
    else:
        months = [(now.year, now.month)]

    print(f"Descargando {len(months)} mes(es)...")
    for y, m in months:
        download_month(y, m)
        download_ajustes(y, m)

    print(f"\nListo: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
