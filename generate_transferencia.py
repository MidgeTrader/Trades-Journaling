#!/usr/bin/env python3
"""
Genera seccion HTML al estilo del reporte de trading (cyber-HUD)
mostrando:
  1) Historial Degiro (trades mas antiguos del trading_journal.xlsx)
  2) Transferencia TastyTrade -> Charles Schwab (Mayo 2024)
"""

import csv, os, json, collections
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCHWAB_DIR = os.path.join(SCRIPT_DIR, 'Reports_Schwab')
XLSX_PATH = os.path.expanduser('~/Desktop/trading_journal.xlsx')

# ---------- Cargar datos del xlsx (Degiro + Tasty) ----------
degiro_trades = []
tasty_stock_buys = {}   # sym -> [(date, qty, price, net)]
tasty_stock_sells = {}

try:
    import openpyxl
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb['All Trades']

    for row in ws.iter_rows(min_row=2, values_only=True):
        try:
            vals = list(row)
            num, broker, date, bs, symbol, typ, qty, price, principal, comm, fees, net, desc = vals[:13]
            if qty is None: qty = 0
            qty = float(qty)
            price = float(price) if price else 0
            net = float(net) if net else 0

            if broker == 'Degiro':
                degiro_trades.append({
                    'date': date, 'bs': bs, 'symbol': symbol, 'typ': typ,
                    'qty': qty, 'price': price, 'net': net, 'desc': str(desc or '')
                })
            elif broker == 'Tastyworks' and typ == 'STOCK':
                target = tasty_stock_buys if (bs == 'Buy' or bs == 'B') else tasty_stock_sells
                target.setdefault(symbol, []).append((date, qty, price, net, str(desc or '')))
        except:
            continue
except Exception as e:
    print(f"⚠️ Error leyendo {XLSX_PATH}: {e}")

# ---------- Calcular netos Tasty ----------
tasty_net = {}
for sym in set(list(tasty_stock_buys.keys()) + list(tasty_stock_sells.keys())):
    b = sum(t[1] for t in tasty_stock_buys.get(sym, []))
    s = sum(t[1] for t in tasty_stock_sells.get(sym, []))
    tasty_net[sym] = round(b - s, 2)

transferred_syms = [s for s, n in tasty_net.items() if n > 0]

# ---------- Leer Schwab CSVs ----------
schwab_trades = collections.defaultdict(list)

for fname in sorted(os.listdir(SCHWAB_DIR)):
    if not fname.endswith('.csv'): continue
    fpath = os.path.join(SCHWAB_DIR, fname)
    try:
        with open(fpath, newline='') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 8: continue
                date, action, symbol, desc, qty, price, fees, amount = row[:8]
                try:
                    qty_f = float(qty) if qty else 0
                except:
                    qty_f = 0
                schwab_trades[symbol].append({
                    'file': fname, 'date': date, 'action': action,
                    'qty': qty_f, 'price': price, 'amount': amount, 'desc': desc
                })
    except:
        continue

# ---------- Armar datos de transferencia ----------
transfer_data = {}  # sym -> {}
for sym in sorted(transferred_syms):
    t_buys = tasty_stock_buys.get(sym, [])
    t_sells = tasty_stock_sells.get(sym, [])
    net_qty = tasty_net[sym]
    if net_qty <= 0: continue

    # Buscar Security Transfer / Journal en Schwab
    s_trades = schwab_trades.get(sym, [])
    has_transfer = any('Transfer' in t['action'] or 'Journal' in t['action'] for t in s_trades)
    if not has_transfer and net_qty > 0:
        # No transfer found - skip (still at Tasty or elsewhere)
        continue

    # Costo total en Tasty
    total_cost = sum(abs(t[3]) for t in t_buys)
    avg_cost = total_cost / net_qty if net_qty else 0

    # Venta en Schwab
    schwab_sells = [t for t in s_trades if t['action'] == 'Sell' and t['qty'] > 0]
    total_proceeds = sum(float(t['amount'].replace('$','').replace(',','')) for t in schwab_sells if t['amount'])
    total_sold_qty = sum(t['qty'] for t in schwab_sells)
    avg_sell = total_proceeds / total_sold_qty if total_sold_qty else 0
    pnl = round(total_proceeds - total_cost, 2)
    pnl_class = 'positive' if pnl >= 0 else 'negative'

    transfer_data[sym] = {
        'net_qty': int(net_qty),
        'total_cost': round(total_cost, 2),
        'avg_cost': round(avg_cost, 2),
        'total_proceeds': round(total_proceeds, 2),
        'avg_sell': round(avg_sell, 2),
        'total_sold_qty': int(total_sold_qty),
        'pnl': pnl,
        'pnl_class': pnl_class,
        'schwab_sells': schwab_sells,
        'tasty_buys': t_buys,
        'transfer_date': '2024-05-01'
    }

# ---------- Stats Degiro ----------
degiro_buys = sum(t['net'] for t in degiro_trades if 'Buy' in t['bs'])
degiro_sells = sum(t['net'] for t in degiro_trades if 'Sell' in t['bs'])
degiro_net = round(degiro_sells + degiro_buys, 2)
degiro_symbols = len(set(t['symbol'] for t in degiro_trades))
degiro_dates = [t['date'] for t in degiro_trades if t['date']]
degiro_start = min(degiro_dates) if degiro_dates else '?'
degiro_end = max(degiro_dates) if degiro_dates else '?'

# ---------- Generar HTML ----------
total_cost_all = sum(d['total_cost'] for d in transfer_data.values())
total_proceeds_all = sum(d['total_proceeds'] for d in transfer_data.values())
total_pnl_all = sum(d['pnl'] for d in transfer_data.values())
total_shares = sum(d['net_qty'] for d in transfer_data.values())
total_pnl_all_class = 'positive' if total_pnl_all >= 0 else 'negative'

html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Transferencia TastyTrade → Schwab</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg-color: #030712;
        --card-bg: rgba(3, 7, 18, 0.7);
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --accent-primary: #00d4ff;
        --accent-primary-dim: rgba(0, 212, 255, 0.15);
        --accent-green: #39ff14;
        --accent-red: #ff003c;
        --accent-blue: #00d4ff;
        --border-color: rgba(0, 212, 255, 0.3);
        --border-glow: 0 0 10px rgba(0, 212, 255, 0.2), inset 0 0 10px rgba(0, 212, 255, 0.1);
        --hover-bg: rgba(0, 212, 255, 0.1);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Rajdhani', sans-serif;
        padding: 2rem;
        min-height: 100vh;
    }}

    h1, h2, h3, .card-title {{
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}

    .container {{
        max-width: 1200px;
        margin: 0 auto;
    }}

    /* Header */
    .header {{
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        box-shadow: var(--border-glow);
        position: relative;
        overflow: hidden;
    }}
    .header::before, .header::after {{
        content: ''; position: absolute; width: 15px; height: 15px;
        border: 2px solid var(--accent-primary);
    }}
    .header::before {{ top: -1px; left: -1px; border-right: none; border-bottom: none; }}
    .header::after {{ bottom: -1px; right: -1px; border-left: none; border-top: none; }}

    .header h1 {{
        font-size: 2rem;
        background: linear-gradient(to right, #60a5fa, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }}
    .header p {{
        color: var(--text-secondary);
        font-size: 1.1rem;
    }}

    /* Section */
    .section-title {{
        font-size: 1.2rem;
        color: var(--accent-primary);
        margin: 2rem 0 1.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
        text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}

    /* Grid */
    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }}

    /* Card */
    .card {{
        background-color: var(--card-bg);
        backdrop-filter: blur(10px);
        border-radius: 4px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--border-glow);
        position: relative;
        overflow: hidden;
    }}
    .card::before, .card::after {{
        content: ''; position: absolute; width: 10px; height: 10px;
        border: 2px solid var(--accent-primary); transition: all 0.3s;
    }}
    .card::before {{ top: -1px; left: -1px; border-right: none; border-bottom: none; }}
    .card::after {{ bottom: -1px; right: -1px; border-left: none; border-top: none; }}
    .card:hover::before, .card:hover::after {{ width: 20px; height: 20px; box-shadow: 0 0 10px var(--accent-primary); }}

    .card-title {{
        color: var(--accent-primary);
        font-size: 0.7rem;
        margin-bottom: 0.75rem;
        text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
    }}
    .card-value {{
        font-family: 'Space Mono', monospace;
        font-size: 1.75rem;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
    }}
    .positive {{ color: var(--accent-green) !important; text-shadow: 0 0 10px rgba(57, 255, 20, 0.4) !important; }}
    .negative {{ color: var(--accent-red) !important; text-shadow: 0 0 10px rgba(255, 0, 60, 0.4) !important; }}
    .neutral {{ color: var(--text-secondary) !important; }}

    .card .sub {{
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 0.25rem;
    }}

    /* Table */
    .table-wrap {{
        overflow-x: auto;
        margin-bottom: 2rem;
    }}
    table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.9rem;
    }}
    th, td {{
        padding: 0.85rem;
        border-bottom: 1px solid rgba(0, 212, 255, 0.15);
        text-align: left;
    }}
    th {{
        color: var(--accent-primary);
        font-family: 'Orbitron', sans-serif;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        background: rgba(0, 212, 255, 0.05);
        white-space: nowrap;
    }}
    tr:hover td {{ background-color: rgba(0, 212, 255, 0.05); }}

    /* Detail rows in Schwab table */
    td.subrow {{
        font-size: 0.8rem;
        color: var(--text-secondary);
        padding: 0.4rem 0.85rem;
    }}
    tr.sub {{
        opacity: 0.7;
    }}
    tr.sub td {{
        border-bottom: 1px solid rgba(0, 212, 255, 0.07);
    }}

    .badge {{
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 600;
        font-family: 'Orbitron', sans-serif;
    }}
    .badge-cyan {{ background: rgba(0,212,255,0.15); color: var(--accent-primary); }}
    .badge-green {{ background: rgba(57,255,20,0.15); color: var(--accent-green); }}
    .badge-red {{ background: rgba(255,0,60,0.15); color: var(--accent-red); }}

    .flow-arrow {{
        color: var(--accent-primary);
        font-size: 1.2rem;
        margin: 0 0.5rem;
        opacity: 0.6;
    }}

    .summary-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;
        padding: 1rem;
        background: var(--hover-bg);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        margin: 1rem 0;
    }}

    hr {{
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 2rem 0;
    }}

    .footer {{
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid var(--border-color);
    }}

    @media (max-width: 768px) {{
        body {{ padding: 1rem; }}
        .grid {{ grid-template-columns: 1fr 1fr; }}
    }}
</style>
</head>
<body>
<div class="container">

    <!-- HEADER -->
    <div class="header">
        <h1>⚡ TRANSFERENCIA TASTYTRADE → CHARLES SCHWAB</h1>
        <p>Análisis de posiciones compradas en TastyTrade, transferidas vía ACATS (01-May-2024) y vendidas en Schwab</p>
    </div>

    <!-- SUMMARY CARDS -->
    <div class="grid">
        <div class="card">
            <div class="card-title">Stocks Transferidos</div>
            <div class="card-value">{len(transfer_data)}</div>
            <div class="sub">símbolos únicos</div>
        </div>
        <div class="card">
            <div class="card-title">Total Acciones</div>
            <div class="card-value">{total_shares}</div>
            <div class="sub">netas transferidas</div>
        </div>
        <div class="card">
            <div class="card-title">Costo Total (Tasty)</div>
            <div class="card-value negative">${total_cost_all:,.2f}</div>
            <div class="sub">compra original</div>
        </div>
        <div class="card">
            <div class="card-title">Producto Venta (Schwab)</div>
            <div class="card-value positive">${total_proceeds_all:,.2f}</div>
            <div class="sub">neto recibido</div>
        </div>
        <div class="card">
            <div class="card-title">P&L Neto</div>
            <div class="card-value {total_pnl_all_class}">${total_pnl_all:,.2f}</div>
            <div class="sub">resultado combinado</div>
        </div>
        <div class="card">
            <div class="card-title">Fecha Transferencia</div>
            <div class="card-value" style="font-size:1.2rem;">2024-05-01</div>
            <div class="sub">Security Transfer ACATS</div>
        </div>
    </div>
'''

# ---------- TABLE: Transferred Stocks ----------
html += '''
    <h2 class="section-title">📦 Posiciones Transferidas</h2>
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>Símbolo</th>
                <th>Qty</th>
                <th>Transferencia</th>
                <th>Costo Tasty</th>
                <th>Precio Medio</th>
                <th>Venta Schwab</th>
                <th>Precio Venta</th>
                <th>P&L</th>
                <th>Rent.</th>
            </tr>
        </thead>
        <tbody>
'''

for sym, d in sorted(transfer_data.items()):
    cost = d['total_cost']
    proceeds = d['total_proceeds']
    pnl = d['pnl']
    pnl_cls = d['pnl_class']
    roi = round((pnl / cost) * 100, 2) if cost else 0
    roi_cls = 'positive' if roi >= 0 else 'negative'

    # Buy details from Tasty
    buy_rows = ''
    for b in d['tasty_buys']:
        buy_rows += f'<tr class="sub"><td colspan="9" class="subrow">└ Tasty Buy: {b[0]} | {int(b[1]):,d} @ ${b[2]:.2f} | Net: ${abs(b[3]):.2f}</td></tr>\n'

    # Sell details from Schwab
    sell_rows = ''
    for s in d['schwab_sells']:
        sell_rows += f'<tr class="sub"><td colspan="9" class="subrow">└ Schwab Sell: {s["date"]} | {int(s["qty"]):,d} @ ${s["price"]} | ${s["amount"]}</td></tr>\n'

    transfer_badge = f'<span class="badge badge-cyan">2024-05-01</span>'

    html += f'''
        <tr>
            <td><strong style="color:var(--accent-primary);">{sym}</strong></td>
            <td>{d["net_qty"]}</td>
            <td>{transfer_badge}</td>
            <td class="negative">${cost:,.2f}</td>
            <td>${d["avg_cost"]:.2f}</td>
            <td class="positive">${proceeds:,.2f}</td>
            <td>${d["avg_sell"]:.2f}</td>
            <td class="{pnl_cls}"><strong>${pnl:,.2f}</strong></td>
            <td class="{roi_cls}">{roi:+.2f}%</td>
        </tr>
        {buy_rows}
        {sell_rows}
    '''

html += '''
        </tbody>
    </table>
    </div>
'''

# ---------- DEGIRO SECTION ----------
html += f'''
    <hr>
    <h2 class="section-title">📜 Historial Degiro (Trades Antiguos)</h2>
    <p style="color:var(--text-secondary); margin-bottom:1.5rem;">
        Datos del archivo <code style="color:var(--accent-primary);">trading_journal.xlsx</code> —
        hoja <strong>All Trades</strong>, filtro Degiro. Período: {degiro_start} → {degiro_end}
    </p>

    <div class="grid">
        <div class="card">
            <div class="card-title">Total Trades</div>
            <div class="card-value">{len(degiro_trades)}</div>
            <div class="sub">{degiro_symbols} símbolos distintos</div>
        </div>
        <div class="card">
            <div class="card-title">Total Compras</div>
            <div class="card-value negative">${abs(degiro_buys):,.2f}</div>
        </div>
        <div class="card">
            <div class="card-title">Total Ventas</div>
            <div class="card-value positive">${degiro_sells:,.2f}</div>
        </div>
        <div class="card">
            <div class="card-title">Net P&L Degiro</div>
            <div class="card-value {"positive" if degiro_net >= 0 else "negative"}">${degiro_net:,.2f}</div>
        </div>
    </div>
'''

# Degiro top symbols by volume
from collections import Counter
degiro_sym_count = Counter(t['symbol'] for t in degiro_trades)
degiro_top = degiro_sym_count.most_common(15)

html += '''
    <div class="table-wrap">
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>ISIN / Símbolo</th>
                <th>Trades</th>
                <th>Compras</th>
                <th>Ventas</th>
                <th>Qty Total</th>
                <th>Net P&L</th>
            </tr>
        </thead>
        <tbody>
'''

degiro_sym_stats = {}
for t in degiro_trades:
    s = t['symbol']
    if s not in degiro_sym_stats:
        degiro_sym_stats[s] = {'buys': 0, 'sells': 0, 'buy_qty': 0, 'sell_qty': 0, 'buy_val': 0, 'sell_val': 0, 'desc': t['desc']}
    if 'Buy' in t['bs']:
        degiro_sym_stats[s]['buys'] += 1
        degiro_sym_stats[s]['buy_qty'] += t['qty']
        degiro_sym_stats[s]['buy_val'] += abs(t['net'])
    else:
        degiro_sym_stats[s]['sells'] += 1
        degiro_sym_stats[s]['sell_qty'] += t['qty']
        degiro_sym_stats[s]['sell_val'] += t['net']

for i, (sym, cnt) in enumerate(degiro_top, 1):
    st = degiro_sym_stats.get(sym, {})
    total_qty = st.get('buy_qty', 0) - st.get('sell_qty', 0)
    net_pnl = st.get('sell_val', 0) - st.get('buy_val', 0)
    pnl_cls = 'positive' if net_pnl >= 0 else 'negative'
    desc_short = (st.get('desc', '') or '')[:35]
    html += f'''
        <tr>
            <td>{i}</td>
            <td><strong style="color:var(--accent-primary);">{sym}</strong><br><span style="font-size:0.75rem;color:var(--text-secondary);">{desc_short}</span></td>
            <td>{st.get('buys',0)+st.get('sells',0)}</td>
            <td>{st.get('buys',0)}</td>
            <td>{st.get('sells',0)}</td>
            <td>{total_qty:,.0f}</td>
            <td class="{pnl_cls}">${net_pnl:,.2f}</td>
        </tr>
    '''

html += '''
        </tbody>
    </table>
    </div>
'''

# ---------- TASTY STOCKS NOT TRANSFERRED ----------
remaining = {s: n for s, n in tasty_net.items() if n > 0 and s not in transfer_data}
if remaining:
    html += '''
    <hr>
    <h2 class="section-title">⚠️ Posiciones Tasty sin vender (no transferidas a Schwab)</h2>
    <p style="color:var(--text-secondary); margin-bottom:1rem;">
        Estas acciones se compraron en TastyTrade, no se vendieron allí, pero tampoco aparecen en la transferencia a Schwab.
        Posiblemente aún estén en TastyTrade o se transfirieron a otro broker.
    </p>
    <div class="table-wrap">
    <table>
        <thead>
            <tr><th>Símbolo</th><th>Qty Restante</th><th>Detalle</th></tr>
        </thead>
        <tbody>
    '''
    for sym in sorted(remaining.keys()):
        n = int(remaining[sym])
        buys = tasty_stock_buys.get(sym, [])
        details = '; '.join(f'{int(b[1])} @ ${b[2]:.2f} ({b[0]})' for b in buys)
        html += f'''
        <tr>
            <td><strong style="color:var(--accent-primary);">{sym}</strong></td>
            <td>{n}</td>
            <td style="font-size:0.85rem;color:var(--text-secondary);">{details}</td>
        </tr>
        '''
    html += '''
        </tbody>
    </table>
    </div>
    '''

# ---------- P&L Mensual Degiro del xlsx ----------
html += '''
    <hr>
    <h2 class="section-title">📊 P&L Mensual — Degiro</h2>
    <div class="table-wrap">
    <table>
        <thead>
            <tr><th>Mes</th><th>Compras</th><th>Ventas</th><th>P&L</th></tr>
        </thead>
        <tbody>
'''

degiro_monthly = collections.OrderedDict()
for t in degiro_trades:
    if t['date']:
        m = t['date'][:7]  # YYYY-MM
        if m not in degiro_monthly:
            degiro_monthly[m] = {'buys': 0, 'sells': 0}
        if 'Buy' in t['bs']:
            degiro_monthly[m]['buys'] += abs(t['net'])
        else:
            degiro_monthly[m]['sells'] += t['net']

for m in sorted(degiro_monthly.keys()):
    d = degiro_monthly[m]
    pnl = d['sells'] - d['buys']
    pnl_cls = 'positive' if pnl >= 0 else 'negative'
    html += f'''
        <tr>
            <td>{m}</td>
            <td class="negative">${d['buys']:,.2f}</td>
            <td class="positive">${d['sells']:,.2f}</td>
            <td class="{pnl_cls}"><strong>${pnl:,.2f}</strong></td>
        </tr>
    '''

html += f'''
        </tbody>
    </table>
    </div>
'''

# ---------- FOOTER ----------
html += f'''
    <div class="footer">
        Generado el {datetime.now().strftime("%Y-%m-%d %H:%M")} ·
        Fuente: trading_journal.xlsx + Reports_Schwab ·
        <span style="color:var(--accent-primary);">Reportes_Brokers</span>
    </div>
</div>
</body>
</html>
'''

# ---------- Guardar ----------
out_path = os.path.join(SCRIPT_DIR, 'transferencia_tasty_schwab.html')
with open(out_path, 'w') as f:
    f.write(html)

print(f"✅ Reporte generado: {out_path}")
print(f"   {len(transfer_data)} stocks transferidos, {total_shares} acciones")
print(f"   P&L total: ${total_pnl_all:,.2f}")
