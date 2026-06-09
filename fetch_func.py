# fetch_func.py
import threading
import urllib.request
import json
import time                  # ← was missing

# ── Configuration ──────────────────────────────────────────────────────────────
PICO_IP  = "10.167.100.98"   # ← put the real IP here (check Pico serial output)
PICO_URL = f"http://{PICO_IP}/estado"
INTERVALO = 5

# ── Core fetch function ────────────────────────────────────────────────────────
def obtener_estado_pico() -> dict | None:
    try:
        with urllib.request.urlopen(PICO_URL, timeout=3) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except Exception as e:
        print(f"[Pico] Error al obtener estado: {e}")
        return None

# ── Sync into GUI state (imported from main) ───────────────────────────────────
def sincronizar_con_pico(stock, ventas, actualizar_pantalla):
    datos = obtener_estado_pico()
    if datos is None:
        return

    cantidades = datos.get("cantidades", {})
    ventas_raw = datos.get("ventas",     {})

    for i in range(3):
        key = str(i + 1)
        if key in cantidades:
            stock[i]  = cantidades[key]
        if key in ventas_raw:
            ventas[i] = ventas_raw[key]

    actualizar_pantalla()
    print(f"[Pico] Sincronizado — stock: {stock}, ventas: {ventas}")

# ── Background polling loop ────────────────────────────────────────────────────
def _loop_sincronizacion(stock, ventas, actualizar_pantalla):
    while True:
        sincronizar_con_pico(stock, ventas, actualizar_pantalla)
        time.sleep(INTERVALO)

def iniciar_sincronizacion(stock, ventas, actualizar_pantalla):
    t = threading.Thread(
        target=_loop_sincronizacion,
        args=(stock, ventas, actualizar_pantalla),
        daemon=True
    )
    t.start()
    print(f"[Pico] Sincronización iniciada → {PICO_URL} cada {INTERVALO}s")