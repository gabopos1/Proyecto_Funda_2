import requests
def obtener_tipo_cambio():
    url = "https://api.hacienda.go.cr/indicadores/tc/dolar"
    try:
        respuesta = requests.get(url, timeout=5)
        datos = respuesta.json()
        return datos["venta"]["valor"]
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return None
if __name__ == '__main__':
    print(f"Prueba de conexión: ₡{obtener_tipo_cambio()}")