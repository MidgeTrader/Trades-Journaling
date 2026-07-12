"""Constantes compartidas del proyecto Reportes_Brokers.

Todas las rutas, parámetros de validación, nombres de columna y
configuración de red centralizadas aquí para evitar duplicación.
"""

import os
import stat
from datetime import datetime

# ── Rutas base ──────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

SCHWAB_DIR = os.path.join(DATA_DIR, "Reports_Schwab")
ALARIC_DIR = os.path.join(DATA_DIR, "Reports_PropReports")
METATRADER_DIR = os.path.join(DATA_DIR, "Reports_MetaTrader")
DAS_DIR = os.path.join(DATA_DIR, "Reports_DAS")
TOS_DIR = os.path.join(DATA_DIR, "Reports_TOS")
GENERIC_DIR = os.path.join(DATA_DIR, "Reports_Generic")
GASTOS_DIR = os.path.join(DATA_DIR, "Reports_Gastos")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "Reports_Screenshots")
HISTORIAL_DEGIRO_DIR = os.path.join(DATA_DIR, "Historial_Degiro")
DIARY_DIR = os.path.expanduser("~/Documents/2026/Diario de Trading")

OUTPUT_FILE = os.path.join(DATA_DIR, "trading_report.html")
TAGS_FILE = os.path.join(DATA_DIR, "tags.json")

SRC_DIR = os.path.join(SCRIPT_DIR, "src")
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")
ENV_PATH = os.path.join(SCRIPT_DIR, ".env")

DOWNLOADER_SCRIPT = os.path.join(SRC_DIR, "download_alaric.py")
GENERATOR_SCRIPT = os.path.join(SRC_DIR, "generate_report.py")
SYNC_SCREENSHOTS_SCRIPT = os.path.join(ASSETS_DIR, "sync_screenshots.sh")

# ── Servidor HTTP ──────────────────────────────────────────────────────────

TAGS_SERVER_PORT = 8765

# ── PropReports API ─────────────────────────────────────────────────────────

PROPREPORTS_BASE_URL = "https://alaric.propreports.com"
PROPREPORTS_LOGIN_RETRIES = 3
PROPREPORTS_LOGIN_BACKOFF = [2, 4, 6]  # segundos entre reintentos
PROPREPORTS_TIMEOUT = 30
PROPREPORTS_TIMEOUT_AJUSTES = 60

# ── Nombres de meses / días ────────────────────────────────────────────────

MESES_ES = [
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

DIAS_SEMANA = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# ── Formatos de fecha ──────────────────────────────────────────────────────

FMT_MDY_HMS = ["%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]
FMT_DMY_HMS = ["%d/%m/%y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
FMT_MDY = ["%m/%d/%Y", "%m/%d/%y"]
FMT_DMY = ["%d/%m/%Y", "%d/%m/%y"]
FMT_YMD_HMS = ["%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]
FMT_YMD_HM = ["%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M"]

FMT_TIME_ONLY = ["%H:%M:%S", "%H:%M"]

ALL_DATE_FORMATS = FMT_MDY_HMS + FMT_DMY_HMS + FMT_MDY + FMT_DMY
ALARIC_OPENED_FORMATS = FMT_MDY_HMS + FMT_DMY_HMS + FMT_MDY + FMT_DMY
ALARIC_CLOSED_FORMATS = FMT_MDY_HMS + FMT_DMY_HMS + FMT_MDY + FMT_DMY

EXPENSE_DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y"]

# ── Columnas de fees en CSVs ───────────────────────────────────────────────

ALARIC_FEE_COLS = ["Comm", "Ecn Fee", "SECTAF", "NSCC", "CL"]
DAS_FEE_COLS = ["Commission", "Executed", "Fees", "SEC", "TAF"]
TOS_FEE_COLS = [
    "COMMISSION/FEE",
    "COMMISSION",
    "FEES",
    "Commission/Fee",
    "Comm",
]

# ── Cabeceras target para CSV normalizado de Alaric ────────────────────────

ALARIC_TARGET_HEADERS = [
    "Opened",
    "Closed",
    "Held",
    "Account",
    "Symbol",
    "Type",
    "CCY",
    "Entry",
    "Exit",
    "Qty",
    "Gross",
    "Comm",
    "Ecn Fee",
    "SECTAF",
    "NSCC",
    "CL",
    "TTC",
    "ATNET",
    "TAG",
    "Weekday",
]

# ── Límites de validación ──────────────────────────────────────────────────

SYMBOL_MAX_LEN = 40
SYMBOL_ALLOWED_CHARS = ".-_"

QTY_MIN = 1
QTY_MAX = 10_000_000

PRICE_MIN = 0.0
PRICE_MAX = 10_000_000.0

DATE_MIN = datetime(2000, 1, 1)
DATE_MAX = datetime(2100, 1, 1)

# ── .env (permisos) ────────────────────────────────────────────────────────

ENV_FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR  # 0o600

# ── Años históricos por defecto ───────────────────────────────────────────

DEFAULT_HISTORICAL_YEARS = [2025, 2026]
