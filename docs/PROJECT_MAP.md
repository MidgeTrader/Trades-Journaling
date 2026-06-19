# Project Map — Reportes_Brokers
*Generado: 2026-06-13*

## 📊 Resumen
| Métrica | Valor |
|---|---|
| Archivos Python | 5 |
| Clases | 3 |
| Funciones/métodos | 68 |
| APIs/servicios externos | 1 |
| Paquetes pip | 11 |

## 🚀 Entry Points
- `actualizar_reporte.py::main`
- `download_alaric.py::main`
- `generate_report.py::main`
- `setup.py::main`

## 🔗 Dependencias entre archivos
```mermaid
graph LR;
```

## 📁 Archivos
| Archivo | Clases | Funciones | APIs detectadas | LOCs |
|---|---|---|---|---|
| `actualizar_reporte.py` | 1 | 6 | — | 147 |
| `download_alaric.py` | 0 | 7 | — | 361 |
| `generate_report.py` | 2 | 42 | pandas | 4454 |
| `generate_transferencia.py` | 0 | 0 | — | 661 |
| `setup.py` | 0 | 2 | — | 154 |

## 🏛️ Clases
| Clase | Archivo | Métodos | Hereda de |
|---|---|---|---|
| `TagServerHandler` | `actualizar_reporte.py` | __init__, do_POST, log_message | SimpleHTTPRequestHandler |
| `Trade` | `generate_report.py` | __init__, __eq__, __hash__ | — |
| `ClosedTrade` | `generate_report.py` | __init__, trade_id, to_dict, __eq__, __hash__ | — |

## 🌐 APIs y Servicios Externos
| Servicio | Tipo |
|---|---|
| `pandas` | data |

## 📦 Paquetes Externos
```
base64
calendar
csv
getpass
http
openpyxl
requests
stat
subprocess
webbrowser
xlrd
```

## 🧠 Para Claude (memoria rápida)

Relaciones clave del proyecto:
- **`actualizar_reporte.py`** | deps: http, subprocess, webbrowser
- **`download_alaric.py`** | deps: calendar, requests, stat, xlrd
- **`generate_report.py`** | APIs: pandas | deps: base64, calendar, csv, stat
- **`generate_transferencia.py`** | deps: csv, openpyxl
- **`setup.py`** | deps: getpass, stat

---
*Generado por [graphify-lite](https://github.com/safishamsi/graphify). 5 archivos analizados.*