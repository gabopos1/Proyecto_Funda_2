import threading
import socket
import json
import time

#Configuracion
PICO_IP   = "10.167.100.98"
PICO_PORT = 80
INTERVALO = 5

#Request del socket raw
def _pico_get(ruta: str) -> dict | None: #Type Hint flecha y :, información pura
    """
    Hace uso de protocolo TCP, peticiones HTTP crudas, Serialización y Deserialización de JSONS Chunking
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET - usará direcciones IPv4, SOCK_STREAM define que será TCP
        sock.settimeout(5) #Tiempo límite de 5 segundos
        sock.connect((PICO_IP, PICO_PORT)) #Se conecta usando las variables anteriormente definidas

        request = (                     #Escribe textualmente el protocolo HTTP/1.1, reconstruye lo que haría requests
            f"GET {ruta} HTTP/1.1\r\n"  #GET - Método HTTP, HTTP/1.1 es versión.
            f"Host: {PICO_IP}\r\n"      #Especifica la dirección IP (o dominio) del servidor al que se le hace el get
            "Connection: close\r\n"     
            "\r\n"
        )                         
        sock.sendall(request.encode("utf-8")) #Se hace petición y por medio de .encode("utf-8") se pasa a binario

        respuesta = b""     #Settea variable binaria vacía
        while True:
            chunk = sock.recv(1024)     #Lee respuesta de la Pico W en bloques de máximo 1024 bytes
            if not chunk:               #Al finalizar conexión con "Connection: close\r\n" chunk es vacío y se cierra el ciclo
                break
            respuesta += chunk          #Va agregando todos los chunks

        sock.close()                    #Cierra el socket

        raw = respuesta.decode("utf-8")         #Convierte la serie de chunks a binario
        body = raw.split("\r\n\r\n", 1)[1].strip() if "\r\n\r\n" in raw else raw.strip()  #Asunto de HTTP y limpieza
        #Método split corta los remanentes de HTTP, generando dos listas, parametro 1 indica que solo debe cortar 1 vez
        return json.loads(body)     #Carga todo lo anterior en un json para leerlo después

    except Exception as e:
        print(f"[Pico] Error en {ruta}: {e}")
        return None

#API
def obtener_estado_pico() -> dict | None:
    """GET /estado → {"cantidades": {…}, "ventas": {…}}""" #Esta es la petición HTTP resultante de la llamada
    return _pico_get("/estado")

def enviar_mantenimiento(activar: bool) -> bool:      #Función Switch
    """
    GET /mantenimiento_on or /mantenimiento_off 
    True si la Pico confirmó el cambio, falso en caso contrario 
    """
    ruta = "/mantenimiento_on" if activar else "/mantenimiento_off"  #Operador ternario, dependiendo del estado de activar (True o False) decide que ruta usar
    resp = _pico_get(ruta)
    if resp and "mantenimiento" in resp:            #Si resp no está vacío y contiene mant - True (FUNCIONÓ)
        print(f"[Pico] Mantenimiento: {resp['mantenimiento']}")     
        return True
    return False                                        #Gestión de errores

def enviar_restock() -> bool:
    """
    esetea los contadores de los motores a 9 
    y abre el archivo de texto interno del chip (cantidades.txt) para sobreescribirlo.
    Retorna True si es exitoso.
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

    for i in range(3):          #Pasa de diccionario (indice key, por str), a lista
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
    t = threading.Thread(               #Inicia evento de tipo hilo para sincronizar sin afectar el resto del sistema
        target=_loop_sincronizacion,    #Ejecuta el target de fondo siempre
        args=(stock, ventas, actualizar_pantalla),          #Argumentos de la función
        daemon=True                 #
    )
    t.start()                   #Comienza a ejecutar de forma inmediata
    print(f"[Pico] Sincronización iniciada → http://{PICO_IP}/estado cada {INTERVALO}s")
