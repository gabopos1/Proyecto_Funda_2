import threading
import socket
import json
import time

#Configuracion
PICO_IP   = "10.167.100.98"
PICO_PORT = 80
INTERVALO = 5

#Request del socket raw
def _pico_get(ruta: str) -> dict | None:
    """
    Sends a minimal HTTP GET to the Pico W.
    Uses raw sockets instead of urllib to avoid MicroPython's
    ECONNRESET/WinError10054 caused by chunked/keep-alive headers.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((PICO_IP, PICO_PORT))

        request = (
            f"GET {ruta} HTTP/1.1\r\n"
            f"Host: {PICO_IP}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        sock.sendall(request.encode("utf-8"))

        respuesta = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            respuesta += chunk

        sock.close()

        raw = respuesta.decode("utf-8")
        body = raw.split("\r\n\r\n", 1)[1].strip() if "\r\n\r\n" in raw else raw.strip()
        return json.loads(body)

    except Exception as e:
        print(f"[Pico] Error en {ruta}: {e}")
        return None

#API
def obtener_estado_pico() -> dict | None:
    """GET /estado → {"cantidades": {…}, "ventas": {…}}"""
    return _pico_get("/estado")

def enviar_mantenimiento(activar: bool) -> bool:
    """
    GET /mantenimiento_on or /mantenimiento_off
    Returns True if the Pico confirmed the change, False otherwise.
    """
    ruta = "/mantenimiento_on" if activar else "/mantenimiento_off"
    resp = _pico_get(ruta)
    if resp and "mantenimiento" in resp:
        print(f"[Pico] Mantenimiento: {resp['mantenimiento']}")
        return True
    return False

def enviar_restock() -> bool:
    """
    GET /restock → tells the Pico to reset all cantidades to 9
    and persist them to cantidades.txt.
    Returns True on success.
    """
    resp = _pico_get("/restock")
    if resp and resp.get("restock"):
        print("[Pico] Restock confirmado por el hardware")
        return True
    print("[Pico] Restock falló o no hubo respuesta")
    return False

#Sincronizar
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

#Background polling loop
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
    print(f"[Pico] Sincronización iniciada → http://{PICO_IP}/estado cada {INTERVALO}s")
