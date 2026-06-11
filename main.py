import time
import dearpygui.dearpygui as dpg
from api_hacienda import obtener_tipo_cambio
from fetch_func import iniciar_sincronizacion

precio_colones = 250
productos = ["p1", "p2", "p3"]
stock = [9, 9, 9]
ventas = [0, 0, 0]
modo_mantenimiento = False
tipo_cambio_actual = None

def obtener_tipo_cambio_cache():
    global tipo_cambio_actual
    if tipo_cambio_actual is None:
        tipo_cambio_actual = obtener_tipo_cambio()
    return tipo_cambio_actual

def actualizar_pantalla():
    for i in range(3):
        dpg.set_value(f"texto_stock_{i}", f"Stock: {stock[i]} uds")
        dpg.set_value(f"texto_ventas_{i}", f"Vendido: {ventas[i]}")
    
    tot_ventas = sum(ventas)
    ganancia_crc = tot_ventas * precio_colones
    dpg.set_value("stat_ventas", f"Ventas totales: {tot_ventas}")
    dpg.set_value("stat_colones", f"Ganancias en Colones: {ganancia_crc} CRC")
    tc = obtener_tipo_cambio_cache()
    if tc:
        ganancia_usd = ganancia_crc / tc
        dpg.set_value("stat_tc", f"Tipo de Cambio Actual: {tc} CRC")
        dpg.set_value("stat_dolares", f"Ganancias en Dólares: {ganancia_usd:.2f} USD")
    else:
        dpg.set_value("stat_tc", "Tipo de Cambio Actual: Error API")
        dpg.set_value("stat_dolares", "Ganancias en Dólares: $0.00")

def simular_compra(sender, app_data, user_data):
    if modo_mantenimiento:
        return
    id_producto = user_data
    if stock[id_producto] > 0:
        stock[id_producto] -= 1
        ventas[id_producto] += 1
        actualizar_pantalla()

def toggle_mantenimiento(sender, app_data):
    global modo_mantenimiento
    modo_mantenimiento = app_data
    from fetch_func import enviar_mantenimiento
    enviar_mantenimiento(modo_mantenimiento)
    
    if modo_mantenimiento:
        dpg.set_value("status_text", "ESTADO: MANTENIMIENTO")
        dpg.configure_item("status_text", color=[255, 0, 0])
        for i in range(3):
            dpg.configure_item(f"btn_venta_{i}", enabled=False)
        dpg.configure_item("btn_rellenar", enabled=True)
    else:
        dpg.set_value("status_text", "ESTADO: OPERATIVO")
        dpg.configure_item("status_text", color=[0, 255, 0])
        for i in range(3):
            dpg.configure_item(f"btn_venta_{i}", enabled=True)
        dpg.configure_item("btn_rellenar", enabled=False)

def resetear_maquina():
    from fetch_func import enviar_restock
    if enviar_restock():
        for i in range(3):
            stock[i] = 9
        actualizar_pantalla()

dpg.create_context()

with dpg.window(tag="VentanaPrincipal"):
    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True):
        dpg.add_table_column(label="1. INVENTARIO", width_stretch=True)
        dpg.add_table_column(label="2. ESTADÍSTICAS", width_stretch=True)
        dpg.add_table_column(label="3. CONTROL", width_stretch=True)
 
        with dpg.table_row():
            with dpg.group():
                for i in range(3):
                    dpg.add_text(f"> {productos[i]}", color=[0, 200, 255])
                    dpg.add_text(f"Stock: 9 uds", tag=f"texto_stock_{i}")
                    dpg.add_button(label="Simular Venta", tag=f"btn_venta_{i}", user_data=i, callback=simular_compra)
                    dpg.add_spacer(height=10)
            
            with dpg.group():
                dpg.add_text("Ventas por producto:", color=[255, 255, 0])
                for i in range(3):
                    dpg.add_text(f"Vendido: 0", tag=f"texto_ventas_{i}")
                dpg.add_separator()
                dpg.add_spacer(height=5)
                dpg.add_text("Totales Históricos:", color=[255, 255, 0])
                dpg.add_text("Ventas totales: 0", tag="stat_ventas")
                dpg.add_spacer(height=5)
                dpg.add_text("Tipo de Cambio: Esperando...", tag="stat_tc", color=[200, 200, 200])
                dpg.add_text("Ganancias en Colones: 0 CRC", tag="stat_colones", color=[0, 255, 0])
                dpg.add_text("Ganancias en Dólares: 0.00 USD", tag="stat_dolares", color=[0, 255, 0])
 
            with dpg.group():
                dpg.add_text("ESTADO: OPERATIVO", tag="status_text", color=[0, 255, 0])
                dpg.add_spacer(height=10)
                dpg.add_checkbox(label="Modo Mantenimiento", callback=toggle_mantenimiento)
                dpg.add_spacer(height=20)
                dpg.add_separator()
                dpg.add_spacer(height=5)
                dpg.add_text("Administración:")
                dpg.add_button(label="Rellenar Máquina", tag="btn_rellenar", callback=resetear_maquina, enabled=False)
 
dpg.create_viewport(title='Administrador Vending Machine', width=800, height=400)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("VentanaPrincipal", True)
 
actualizar_pantalla()
iniciar_sincronizacion(stock, ventas, actualizar_pantalla)
 
dpg.start_dearpygui()
dpg.destroy_context()
