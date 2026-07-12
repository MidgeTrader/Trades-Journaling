---
tags: [project/spec]
aliases: [Especificación Reportes_Brokers]
---

# 📋 Reportes_Brokers SPEC

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Estado | Aprobado |
| Owner | Rafael Barbarroja |
| Última actualización | 2026-07-12 |

---

## 0. Glosario

| Término | Definición |
|---|---|
| **PropReports** | Plataforma de reporting para prop trading firms (Alaric Securities) |
| **Alaric Securities** | Prop trading firm, datos descargados vía PropReports API |
| **Matched trade** | Trade cerrado con entrada y salida conocidas (long: compra→venta, short: venta→compra) |
| **FIFO** | First In First Out — método de matching: el primer lote comprado es el primero en venderse |
| **Locates** | Costes de búsqueda/prestamo de acciones para short selling |
| **SECTAF** | SEC + TAF — tasas regulatorias americanas (SEC fee + Trading Activity Fee) |
| **Ticker** | Símbolo cotizado (AAPL, NVDA, etc.) |
| **GEX** | Gamma Exposure — métrica de riesgo de opciones |
| **Drawdown** | Caída desde el pico de equity acumulado |
| **Profit Factor** | Gross Wins / Gross Losses |
| **Win Rate** | % de trades ganadores sobre total |
| **Tag** | Anotación manual asignada a un trade (entrada/salida/nota) |
| **Floating position** | Posición abierta (no cerrada) mostrada en pestaña "Flotante" |
| **Rolling P&L** | Suma acumulada de P&L a lo largo del tiempo |

---

## 1. Propósito

### Objetivo

- **Primario:** Generar un reporte HTML interactivo de performance de trading a partir de múltiples fuentes de datos (brokers, journals, capturas de pantalla)
- **Usuarios objetivo:** Rafael Barbarroja (único usuario)
- **Casos de uso principales:**
  1. Descargar datos mensuales de Alaric Securities (PropReports API)
  2. Leer CSVs de ejecuciones de múltiples brokers (Schwab, Alaric, MetaTrader, DAS, ThinkOrSwim, Generic)
  3. Matchear trades usando FIFO para calcular P&L cerrado
  4. Generar dashboard HTML interactivo con Chart.js (equity curve, drawdown, KPIs)
  5. Asignar tags manuales a trades (persisten en `tags.json`)
  6. Integrar diario de trading Obsidian y screenshots
  7. Registrar gastos fijos mensuales (locates, comisiones)
- **Problema que resuelve:** Unificar datos de múltiples brokers en un solo reporte visual con métricas avanzadas (Sharpe, Sortino, Kelly, SQN, drawdown, streaks)

### No-objetivos

- No es una plataforma de ejecución de órdenes
- No es un reemplazo de contabilidad fiscal
- No soporta trading algorítmico o automatizado
- No tiene autenticación multi-usuario
- No expone API REST externa

### Stakeholders

| Rol | Nombre | Responsabilidad |
|---|---|---|
| Usuario único | Rafael Barbarroja | Operación, tagging, revisión de performance |

### Supuestos y dependencias

- **Dependencias críticas:**
  - PropReports API (Alaric) — requiere credenciales en `.env`
  - Python 3.13+ con `requests`, `xlrd` (XLS parsing)
  - Chart.js vía CDN (requiere internet para el reporte HTML)
- **Supuestos:**
  - Los CSVs de brokers siguen formatos conocidos
  - El diario de trading Obsidian está en `~/Documents/2026/Diario de Trading/`
  - Las capturas de pantalla se sincronizan desde Google Drive vía `rclone`

---

## 2. Requisitos Funcionales

### FR-001 — Descarga automática de Alaric

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Descargar trades cerrados y gastos desde PropReports API para un mes/año específico, convertirlos a CSV con cabeceras normalizadas.

**Criterios de aceptación**
- Dado un mes YYYY-MM válido, descarga el XLS y genera un CSV en `data/Reports_PropReports/`
- Maneja 3 intentos de login con backoff
- Detecta y corrige BOM corrupto en XLS

### FR-002 — Parsing multi-broker

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Leer CSVs de 6 formatos distintos y convertirlos a objetos `Trade` o `ClosedTrade` internos.

**Formatos soportados:**
- Schwab (ejecuciones individuales)
- Alaric/PropReports (trades cerrados)
- MetaTrader 4/5 (Account History)
- DAS Trader (execution log)
- ThinkOrSwim (trade confirmation)
- Generic (mapping.json personalizado)
- Histórico Degiro + Tastyworks (desde `trading_journal.parquet`)

### FR-003 — FIFO Matching

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Dada una lista de ejecuciones (compras/ventas), emparejarlas FIFO para generar `ClosedTrade` con entry/exit price, fees y P&L.

**Criterios de aceptación**
- Compras acumulan lotes, ventas consumen el lote más antiguo
- Soporta partial fills (una venta puede matchear múltiples lotes)
- Calcula entry_fees y exit_fees proporcionales

### FR-004 — Reporte HTML interactivo

- **Prioridad:** Must
- **Estado:** Done
- **Descripción:** Generar `trading_report.html` con dashboard visual que incluye:
  - KPIs (Gross P&L, Net P&L, Profit Factor, Win Rate, Total Trades)
  - Equity curve + drawdown chart (Chart.js)
  - Monthly breakdown
  - Calendario mensual con P&L por día
  - Daily details con desglose trade por trade
  - Tags modal interactivo (click en símbolo → asignar tags)
  - Pestañas: Annual Board, Calendar, Daily Details, Metricas, Flotante, Build Report
  - Customizer: tema de color, modo, idioma (ES/EN)

### FR-005 — Tag system persistente

- **Prioridad:** Should
- **Estado:** Done
- **Descripción:** El usuario puede asignar tags de entrada, salida y notas a trades individuales. Persisten en `data/tags.json` entre regeneraciones.

**Criterios de aceptación**
- Click en símbolo en Daily Details abre modal de tags
- Tags se guardan via POST `/save-tags` (modo servidor) o directamente en `tags.json`
- Tags sobreviven a regeneración del reporte

### FR-006 — Integración Obsidian

- **Prioridad:** Could
- **Estado:** Done
- **Descripción:** Leer entradas del diario de trading desde `~/Documents/2026/Diario de Trading/` y mostrarlas en Daily Details.

**Criterios de aceptación**
- Archivos `Trading_Diary_DD-MM-YYYY.md` se parsean y convierten a HTML
- Soporta YAML frontmatter, wikilinks `[[TICKER]]`, markdown básico
- Se muestra en la vista de detalle del día correspondiente

### FR-007 — Screenshots viewer

- **Prioridad:** Could
- **Estado:** Done
- **Descripción:** Mostrar capturas de pantalla de trades organizadas por fecha y símbolo.

**Criterios de aceptación**
- Escanea `data/Reports_Screenshots/` en busca de imágenes con fecha en el nombre
- Reconoce patrón `SIMBOLO_YYYY-MM-DD-*.png`
- Se muestra en Daily Details asociado a cada día

### FR-008 — Gastos mensuales

- **Prioridad:** Should
- **Estado:** Done
- **Descripción:** Descargar y mostrar gastos fijos (locates, comisiones) desde Alaric.

**Criterios de aceptación**
- CSVs en `data/Reports_Gastos/` con columnas Date, Category, Comment, Debit
- Se restan del P&L diario en el reporte
- Soporta cabecera automática o explícita

---

## 4. Arquitectura

```
actualizar_reporte.py (orquestador)
       │
       ├── src/download_alaric.py (descarga PropReports)
       │       └── PropReports API (XLS → CSV)
       │
       ├── src/generate_report.py (generación HTML)
       │       ├── parseo multi-broker (Schwab, Alaric, MT, DAS, ToS, Generic)
       │       ├── FIFO matching engine
       │       ├── cálculo de KPIs y métricas avanzadas
       │       └── plantilla HTML + Chart.js
       │
       ├── assets/sync_screenshots.sh (rclone → Google Drive)
       │
       └── data/ (CSVs, HTML, tags, screenshots)
                ├── Reports_PropReports/   (Alaric mensual)
                ├── Reports_Schwab/        (Schwab manual)
                ├── Reports_Gastos/        (gastos fijos)
                ├── Reports_Screenshots/   (capturas)
                ├── Historial_Degiro/      (Degiro histórico)
                └── trading_journal.parquet (histórico consolidado)
```

### Stack

- **Lenguaje:** Python 3.13+
- **HTTP Server:** `http.server.HTTPServer` (stdlib, solo para tags)
- **Charting:** Chart.js v4 (CDN, en el HTML)
- **Librerías externas:** `requests`, `xlrd`
- **Datos:** CSV, Parquet (pandas), JSON

### Pipeline de datos

```
PropReports ──XLS──→ download_alaric.py ──CSV──→ generate_report.py ──HTML──→ navegador
Schwab CSV ──────────────────────────────────────→ generate_report.py
MT4/5 CSV ──────────────────────────────────────→ generate_report.py
DAS CSV ─────────────────────────────────────────→ generate_report.py
ToS CSV ─────────────────────────────────────────→ generate_report.py
Generic CSV ─────────────────────────────────────→ generate_report.py
trading_journal.parquet ────────────────────────→ generate_report.py
Obsidian .md ───────────────────────────────────→ generate_report.py
Screenshots ────────────────────────────────────→ generate_report.py
```

### Estructura de Directorios

```
Reportes_Brokers/
├── actualizar_reporte.py      # Orquestador principal
├── src/
│   ├── generate_report.py     # Generación HTML + parsing + cálculos
│   ├── download_alaric.py     # Descarga PropReports
│   └── setup.py               # Configuración inicial interactiva
├── config/
│   ├── requirements.txt
│   └── degiro_cusip_map.json  # Mapeo CUSIP→ticker para Degiro
├── data/                      # Datos de trading (gitignored)
├── assets/
│   ├── midge_logo.png         # Logo del trader
│   └── sync_screenshots.sh    # Script rclone para sincronizar capturas
├── docs/
│   ├── README.md
│   ├── PROJECT_MAP.md
│   └── INSTRUCCIONES_GITHUB.md
├── .env                       # Credenciales (gitignored, 0600)
├── .gitignore
└── SPEC.md                    # Este archivo
```

---

## 6. Manejo de Errores (Estado Actual)

### Prácticas actuales

- **Parsing CSV:** `try/except` alrededor de `csv.DictReader` con `print()` en error. Retorna lista vacía en fallo.
- **Descarga Alaric:** Retry de login con backoff (3 intentos, sleep 2s/6s).
- **Tags:** `try/except` con logging mínimo.
- **Screenshots:** Omite archivos no-imagen silenciosamente.
- **Servidor HTTP:** `try/except` genérico en `POST /save-tags`.

### Problemas conocidos

- No hay logging estructurado (solo `print()`)
- `except: continue` silencioso en varios parsers CSV
- Errores de parsing no tienen trazabilidad (no se sabe qué fila falló)
- No hay distinción entre error de negocio y error de infraestructura

### Taxonomía

| Tipo | Ejemplo | Manejo actual |
|---|---|---|
| Validación | CSV mal formateado | `print()` + retorno lista vacía |
| Red | PropReports caído | Retry 3 intentos, luego `sys.exit(1)` |
| Parseo | Fecha no parseable | `continue` (salta la fila) |
| Archivo | CSV no encontrado | `print()` + lista vacía |

---

## 7. Logging (Estado Actual)

Actualmente todo el logging usa `print()` directo a stdout.

**Qué se loguea:**
- Progreso: "PASO 1/2: Descargando...", "Login exitoso"
- Errores: "Error reading CSV: {e}"
- Debug: "DEBUG: Annual Stats Keys: {keys}"
- Tags: "Tags guardados: {count} trades"

**Qué NO se loguea:**
- Timestamps
- Severidad (todos son prints)
- Contexto (request_id, trade_id, file)
- No hay formato estructurado

**Nunca se loguea:** (correcto)
- Contraseñas
- API keys completas (el user sí aparece en prints)

---

## 11. Modelos de Datos

### Trade

Representa una ejecución individual (compra o venta). Usado en FIFO matching.

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `date` | `datetime` | sí | Fecha de ejecución |
| `symbol` | `str` | sí | Ticker (AAPL, NVDA...) |
| `quantity` | `int` | sí | Número de acciones siempre positivo |
| `price` | `float` | sí | Precio de ejecución |
| `action` | `str` | sí | "Buy" o "Sell" |
| `fees` | `float` | sí | Comisiones de la ejecución |

**Validación:** `_validate_symbol()`, `_validate_quantity()`, `_validate_price()`, `_validate_date()`

### ClosedTrade

Representa un trade cerrado (entrada + salida matched). Es el objeto principal del reporte.

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `symbol` | `str` | sí | Ticker |
| `open_date` | `datetime` | sí | Fecha de apertura |
| `close_date` | `datetime` | sí | Fecha de cierre |
| `quantity` | `int` | sí | Acciones |
| `entry_price` | `float` | sí | Precio de entrada |
| `exit_price` | `float` | sí | Precio de salida |
| `entry_fees` | `float` | sí | Comisiones de entrada |
| `exit_fees` | `float` | sí | Comisiones de salida |
| `direction` | `str` | sí | "Long" o "Short" |
| `tag` | `str` | no | Tag legacy (backwards compat) |
| `entry_tag` | `str` | no | Tag de entrada |
| `exit_tag` | `str` | no | Tag de salida |
| `note` | `str` | no | Nota del trade |
| `gross_pl` | `float` | derivado | `proceeds - cost_basis` (long) o inverso (short) |
| `net_pl` | `float` | derivado | `gross_pl - total_fees` |
| `duration` | `int` | derivado | `close_date - open_date` en días |
| `roi_pct` | `float` | derivado | `net_pl / cost_basis * 100` |

**Clave única (`trade_id`):** `"{symbol}|{open_date}|{entry_price}|{exit_price}|{quantity}"`

### Trade Tags

Persistidos en `data/tags.json`, key = `trade_id`.

```json
{
  "{trade_id}": {
    "entry_tag": "momentum,breakout",
    "exit_tag": "stop_loss",
    "note": "Entré bien pero salí temprano"
  }
}
```

### Formatos CSV Esperados

**Schwab:** Date, Symbol, Quantity, Price, Action, Description, Fees & Comm
**Alaric/PropReports:** Opened, Closed, Symbol, Type, Entry, Exit, Qty, Gross, Comm, Ecn Fee, SECTAF, NSCC, CL, TTC, ATNET, TAG, Weekday
**MetaTrader:** Open Time, Close Time, Item, Size, Price, Close Price, Type, Commission, Swap, Taxes, Comment
**DAS:** Date, Symbol, Side, Quantity, Price, Commission
**ThinkOrSwim:** DATE, SYMBOL, QTY, PRICE, TRANSACTION, COMMISSION/FEE
**Gastos:** Date, Category, Comment, Debit

### Formatos Archivo Histórico

**Parquet (`trading_journal.parquet`):**
- Columnas: Symbol, Date, Side, Qty, Price, Fees, Net_USD, Broker, Type, Strike, Expiry, CUSIP
- Brokers incluidos: Degiro (2020-2021), Tastyworks STOCK (2022-2024), Tastyworks OPTIONS (2022-2024)
- Opciones identificadas por clave compuesta: `SIMBOLO.TIPO.YYMMDD.STRIKE`

---

## 12. Restricciones

- **No hay estado mutable global** — los datos se procesan en memoria y se vuelcan a HTML estático + `tags.json`
- **Sin dependencias circulares** — `actualizar_reporte.py` llama a `download_alaric.py` y `generate_report.py` como subprocesos, nunca hay importación cruzada
- **Sin API pública** — el servidor HTTP es solo para el endpoint `/save-tags`
- **Sin testing automatizado** — el proyecto no tiene tests
- **Sin CI/CD** — ejecución local manual

---

## 13. Seguridad

### Lo que ya está bien

| Práctica | Estado |
|---|---|
| `.env` con permisos `0600` | ✅ `os.chmod(env_path, stat.S_IRUSR \| stat.S_IWUSR)` |
| `.env` en `.gitignore` | ✅ |
| Credenciales nunca hardcodeadas | ✅ via `os.environ.get()` |
| Logo personal nunca se sube | ✅ en `.gitignore` |
| CSV de datos nunca se suben | ✅ en `.gitignore` |

### Lo que se podría mejorar

| Riesgo | Situación actual |
|---|---|
| **Contraseña en texto plano** | PropReports password está en `.env` en texto plano. Riesgo aceptado (solo local) |
| **POST /save-tags sin validación** | Acepta cualquier JSON sin sanitizar (riesgo bajo, solo localhost) |
| **Sin cifrado en reposo** | Datos de trading personales en disco sin cifrar |
| **No hay validación de entorno** | Si `.env` falta, las variables quedan vacías y el error solo aparece al hacer login |

### Gestión de Secrets

```python
# Patrón actual (generate_report.py)
USER = os.environ.get("PROPREPORTS_USER", "")
PASSWORD = os.environ.get("PROPREPORTS_PASSWORD", "")
# Si faltan, se intenta login y falla más tarde
```

---

## 16. Riesgos y Preguntas Abiertas

| Riesgo/Pregunta | Impacto | Estado |
|---|---|---|
| `generate_report.py` monolítico (4,451 líneas) | Mantenibilidad | Abierto — no afecta funcionalidad |
| Sin tests automatizados | Riesgo de regresión | Abierto |
| Dependencia de PropReports API | Si cambia su formato, rompe descarga | Abierto |
| `xlrd` sin mantenimiento activo | Vulnerabilidad potencial | Abierto |
| Credenciales en texto plano en `.env` | Exposición si alguien accede al equipo | Aceptado (solo local) |

---

## 19. Change Log

| Versión | Fecha | Cambios | Autor |
|---|---|---|---|
| v1.0 | 2026-07-12 | Especificación inicial — documentación del proyecto existente | Rafael Barbarroja |
