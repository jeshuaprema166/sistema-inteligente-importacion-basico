# Código 🐜✨
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import pandas as pd
import streamlit as st
import io
from fpdf import FPDF
import os

# --- CONFIGURACIÓN DE SEGURIDAD ---
def verificar_acceso():
    if "PASSWORD_ADMIN" not in st.secrets:
        return True
    if st.session_state.get("autenticado", False):
        return True
    
    # --- PANTALLA DE BIENVENIDA ---
    # Mostrar la imagen de portada corporativa en la parte superior
    st.image("IMG-20261021-WA0005.jpg", use_container_width=True)
    st.markdown("<h1 style='text-align: center;'>Bienvenidos<br>🛳️</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>¿Sabe cuánto le cuesta realmente traer los productos desde el exterior<br> hasta su depósito?<br>Este Sistema Inteligente le revela:</h3>", unsafe_allow_html=True)
    st.markdown("""
    * **La verdad** sobre sus costos de importación, márgenes de utilidad y precios óptimos de venta.
    * **Identificar** los márgenes reales de ganancia antes de nacionalizar, analizando la rentabilidad neta por producto prorrateando con precisión los costos según peso (kg) y volumen (m³). Así sabrá qué productos le dejan ganancia real y cuáles no.
    * **Optimizar** el espacio de su contenedor y evite pérdidas por costos ocultos.
    * **Alarmas** de reposición de inventario 🟢🟡🔴 por IA, que permiten monitorear el comportamiento de las existencias, previniendo el desabastecimiento o sobrecompra, que redunda en estancamiento del Capital económico.
    * **Ingresar** de forma **automática** de **TODOS** los datos y detalles del Excel de sus artículos del inventario al Sistema de Análisis Inteligente de Importación.
    * **Definir fácilmente** y con certeza a qué proveedor del exterior debe comprar, o si es mejor hacerlo localmente. 
    <mark><span style="font-size: 1.0em; white-space: nowrap;">**✨ Todo eso y más, con la ayuda de nuestro Sistema de Importación con IA 🤖 ✨**</span></mark>
    """, unsafe_allow_html=True)
    
    # Texto destacado
    st.markdown("""
    <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; border-left: 5px solid #2196F3; margin-top: 20px; margin-bottom: 20px;">
    <strong>"UN SISTEMA DE COMERCIALIZACIÓN DISEÑADO PARA PROTEGER SU CAPITAL Y ASEGURAR QUE EL NEGOCIO SIEMPRE CREZCA"</strong>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<span style='font-size: 1.5em; white-space: nowrap;'>**Instrucciones:**</span>", unsafe_allow_html=True)
    st.markdown("1. Una vez dentro, vaya al menú desplegable de la izquierda (⏪) para configurar los **Datos de su empresa**: Razón Social (Nombre de la Empresa), RIF y Propietario; márgenes (%) de utilidad y descuentos previstos. **Datos de la Empresa Origen**: País, Nombre de la Empresa, Nro de factura.")
    st.markdown("2. Para ingresar al Sistema, escriba a continuación la contraseña 🔑 suministrada por su Asesor de Importación para comenzar el análisis.")
    
    # --- FIRMA Y FOTO ---
    # Damos 1 espacio vacío, 1 para el texto y 1 para la foto
    col_izq, col_centro, col_der = st.columns([1, 1, 1]) 
    
    with col_centro:
        st.markdown("<h4 style='text-align: center; margin-top: 20px;'>Diseñado y elaborado por<br>su Asesor de Importación Inteligente<br> Prof. Jesús Pulido V.</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Teléfonos de contacto:<br>0424-728.3199 / 0416-291.6426</p>", unsafe_allow_html=True)
        
        # Aquí va la foto, dentro de la columna central
        try:
            st.image("profesor.jpg", width=180) # Ajuste el ancho a su gusto
        except:
            st.write("📷")
    
    st.divider()
    
    # --- CAJA DE CONTRASEÑA ---
    password = st.text_input("Contraseña de acceso", type="password")
    
    if st.button("Ingresar", type="primary"):
        if password == st.secrets["PASSWORD_ADMIN"]:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta. Intente de nuevo.")
        
    return False # actualizado 


CENTAVO = Decimal("0.01")
CERO = Decimal("0")
UNO = Decimal("1")

GASTOS_CONTENEDOR = (
    ("Manejo de Puerto", "peso"),
    ("Flete Terrestre Nacional", "peso"),
    ("Logística Internacional", "volumen"),
    ("Derechos de Aduana", "volumen"),
    ("Gestión Aduanera", "volumen"),
    ("Gastos Administrativos", "volumen"),
)

DEFAULTS = {
    "empresa": "Constructora e Inversiones Los Mangos",
    "rif": "V-189531717",
    "propietario": "Adrian Arellano",
    "margen": 30.0,
    "desc_mayorista": 15.0,
    "desc_especial": 5.0,
    "origen": "",
    "proveedor": "",
    "factura": "",
    "fecha_proximo_pedido": None  # <--- NUEVO
}

def leer_decimal(texto, etiqueta, permitir_cero=True, es_dinero=False):
    normalizado = str(texto).strip().replace(",", ".")
    if not normalizado:
        raise ValueError(f"Completa el campo «{etiqueta}».")
    try:
        valor = Decimal(normalizado)
    except InvalidOperation as error:
        raise ValueError(f"«{etiqueta}» debe ser un número válido; puedes usar punto o coma decimal.") from error
    if not valor.is_finite() or valor < CERO:
        raise ValueError(f"«{etiqueta}» debe ser un valor igual o mayor que cero.")
    if not permitir_cero and valor == CERO:
        raise ValueError(f"«{etiqueta}» debe ser mayor que cero.")
    if es_dinero:
        valor = valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return valor

def formato_dinero(valor):
    valor_redondeado = valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    return f"$ {valor_redondeado:,.2f}"

def redondear_entero(valor):
    return valor.quantize(UNO, rounding=ROUND_HALF_UP)

def prorratear_gasto(monto, productos, campo_base):
    total_centavos = int(monto.quantize(CENTAVO, rounding=ROUND_HALF_UP) * 100)
    bases = [producto[campo_base] for producto in productos]
    suma_bases = sum(bases, CERO)
    if suma_bases <= CERO:
        raise ValueError(f"No hay base suficiente para repartir el gasto por {campo_base}.")
    partes_exactas = [Decimal(total_centavos) * base / suma_bases for base in bases]
    partes_en_centavos = [int(parte) for parte in partes_exactas]
    centavos_sobrantes = total_centavos - sum(partes_en_centavos)
    orden_por_resto = sorted(
        range(len(productos)),
        key=lambda i: partes_exactas[i] - Decimal(partes_en_centavos[i]),
        reverse=True,
    )
    for indice in orden_por_resto[:centavos_sobrantes]:
        partes_en_centavos[indice] += 1
    return [Decimal(parte) / 100 for parte in partes_en_centavos]

def evaluar_semaforo(stock_actual, ventas_semanales, dias_entrega, fecha_proximo_pedido=None):
    from datetime import date
    
    if ventas_semanales <= 0:
        return "⚪", "Sin ventas registradas", 0, 0, False
    
    semanas_stock = stock_actual / ventas_semanales
    semanas_entrega = dias_entrega / 7
    margen = semanas_stock - semanas_entrega
    
    # Sugerido para cubrir entrega + 4 semanas de colchón
    sugerido_ahora = int((semanas_entrega * ventas_semanales) + (4 * ventas_semanales) - stock_actual)
    if sugerido_ahora < 0: sugerido_ahora = 0
    
    sugerido_futuro = 0
    riesgo_quiebre = False
    
    if fecha_proximo_pedido and fecha_proximo_pedido > date.today():
        dias_hasta_pedido = (fecha_proximo_pedido - date.today()).days
        semanas_hasta_pedido = dias_hasta_pedido / 7
        
        demanda_futura = (semanas_hasta_pedido * ventas_semanales) + (semanas_entrega * ventas_semanales) + (4 * ventas_semanales)
        sugerido_futuro = int(demanda_futura - stock_actual)
        if sugerido_futuro < 0: sugerido_futuro = 0
        
        if semanas_stock < semanas_hasta_pedido:
            riesgo_quiebre = True

    if margen <= 0:
        color = "🔴"
        mensaje = "¡ALERTA ROJA! Pedir YA"
    elif margen <= 2:
        color = "🟡"
        mensaje = "Precaución: Pedir pronto"
    else:
        color = "🟢"
        mensaje = "Todo bien: Stock suficiente"
        
    return color, mensaje, sugerido_ahora, sugerido_futuro, riesgo_quiebre

def evaluar_carga_pesada(p):
    precio_china = p.get("precio_china", 0)
    cantidad = p.get("cantidad", 1)
    if cantidad <= 0:
        cantidad = 1
        
    # Calculamos el gasto de arribo unitario sumando los gastos del producto y dividiendo entre la cantidad
    gastos_totales_item = sum(p.get("gastos", {}).values())
    gasto_arribo_unitario = gastos_totales_item / cantidad

    if precio_china <= 0:
        return "⚪", "Sin datos", 0

    # Calcular qué porcentaje del precio es el flete
    porcentaje_flete = (gasto_arribo_unitario / precio_china) * 100

    if porcentaje_flete > 60:
        return "🔴", f"PELIGRO: Flete = {porcentaje_flete:.1f}% del costo.", 0
    elif porcentaje_flete >= 30:
        return "🟡", f"CUIDADO: Flete = {porcentaje_flete:.1f}% del costo.", 0
    else:
        return "🟢", f"RENTABLE: Flete = {porcentaje_flete:.1f}% del costo.", 0
        

def calcular_costos(productos, gastos_ingresados, config):
    margen = Decimal(str(config["margen"])) / Decimal("100")
    desc_mayorista = Decimal(str(config["desc_mayorista"])) / Decimal("100")
    desc_especial = Decimal(str(config["desc_especial"])) / Decimal("100")

    gastos = []
    for nombre_gasto, criterio in GASTOS_CONTENEDOR:
        monto = gastos_ingresados[nombre_gasto]
        gastos.append((nombre_gasto, criterio, monto))
        campo_base = "peso_total" if criterio == "peso" else "volumen_total"
        repartos = prorratear_gasto(monto, productos, campo_base)
        for producto, monto_asignado in zip(productos, repartos):
            producto["gastos"][nombre_gasto] = monto_asignado

    for producto in productos:
        cantidad = producto["cantidad"]
        gastos_totales = sum(producto["gastos"].values(), CERO)
        gasto_unitario = gastos_totales / cantidad
        costo_real = (producto["precio_china"] + gasto_unitario).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        producto["gastos_totales"] = gastos_totales
        producto["gasto_unitario"] = gasto_unitario
        producto["costo_unitario"] = costo_real
        producto["pvp_normal"] = redondear_entero(costo_real / (UNO - margen))
        producto["pvp_mayorista"] = redondear_entero(producto["pvp_normal"] * (UNO - desc_mayorista))
        producto["pvp_especial"] = redondear_entero(producto["pvp_normal"] * (UNO - desc_especial))
    return gastos

def crear_reporte(productos, gastos_contenedor, config):
    encabezado = "\n".join((
        "=" * 72,
        "   SISTEMA DE COSTOS DE IMPORTACIÓN",
        f"   {config['empresa']}",
        f"   RIF: {config['rif']}",
        f"   Propietario: {config['propietario']}",
        "=" * 72,
    ))
    lineas = [encabezado, "", "=" * 72, f"   REPORTE DE COSTOS: {len(productos)} productos", "=" * 72]

    for indice, producto in enumerate(productos, start=1):
        cantidad = producto["cantidad"]
        lineas.extend([
            "", f"PRODUCTO {indice}: {producto['nombre']}", "-" * 72,
            f"   Cantidad de unidades:           {cantidad:>12,}",
            f"   Peso total:                     {producto['peso_total']:>12,.3f} kg",
            f"   Volumen total:                  {producto['volumen_total']:>12,.6f} m3",
            f"   Precio China (por unidad):      {formato_dinero(producto['precio_china'])}",
            f"   Precio China (total):           {formato_dinero(producto['precio_china'] * cantidad)}",
            "", "   GASTOS DE ARRIBO ASIGNADOS:",
        ])
        for nombre_gasto, criterio, _ in gastos_contenedor:
            asignado = producto["gastos"][nombre_gasto]
            por_unidad = asignado / cantidad
            lineas.append(f"      {nombre_gasto} ({criterio}): {formato_dinero(asignado)} total; {formato_dinero(por_unidad)} por unidad")
        lineas.extend([
            "",
            f"   Gastos de arribo (total):        {formato_dinero(producto['gastos_totales'])}",
            f"   Gastos de arribo (por unidad):   {formato_dinero(producto['gasto_unitario'])}",
            f"   COSTO REAL EN ESTANTE (unidad):  {formato_dinero(producto['costo_unitario'])}",
            "   PRECIOS DE VENTA:",
            f"      PVP Normal:                   $ {producto['pvp_normal']:>12,.0f}",
            f"      PVP Mayorista:                $ {producto['pvp_mayorista']:>12,.0f}",
            f"      PVP Especial:                 $ {producto['pvp_especial']:>12,.0f}",
        ])
       
        # --- BLOQUE DEL SEMÁFORO EN EL TEXTO ---
        color, mensaje, sug_ahora, sug_futuro, riesgo = evaluar_semaforo(
            producto.get("stock_actual", 0), 
            producto.get("ventas_semanales", 0), 
            producto.get("dias_entrega", 0),
            config.get("fecha_proximo_pedido")
        )
        lineas.extend([
            f"   SEMÁFORO DE REPOSICIÓN: {color} {mensaje}",
            f"   ====> Pedir AHORA: {sug_ahora} unds",
        ])
        if sug_futuro > 0 and config.get("fecha_proximo_pedido"):
            lineas.append(f"   ====> Para el pedido del {config['fecha_proximo_pedido']}: {sug_futuro} unds")
        if riesgo:
            lineas.append("   ⚠️ ALERTA: Se agota antes del próximo pedido. Buscar proveedor local.")
            
        lineas.append("-" * 72)

        # --- BLOQUE DE CARGA PESADA EN EL TEXTO ---
        color_carga, mensaje_carga, _ = evaluar_carga_pesada(producto)
        lineas.extend([
            f"   EVALUACIÓN DE CARGA: {color_carga} {mensaje_carga}",
            "----------------------------------------"
        ])
            
    cantidad_total = sum(p["cantidad"] for p in productos)
    pvp_normal_total = sum((p["pvp_normal"] * p["cantidad"] for p in productos), CERO)
    pvp_mayorista_total = sum((p["pvp_mayorista"] * p["cantidad"] for p in productos), CERO)
    pvp_especial_total = sum((p["pvp_especial"] * p["cantidad"] for p in productos), CERO)

    lineas.extend([
        "", "=" * 60, "  TABLA RESUMEN", "=" * 60,
        f"  {'Producto':<15s} {'Cant.':>8s} {'Costo U.':>12s} {'PVP Norm.':>12s} {'PVP May.':>12s} {'PVP Esp.':>12s}",
        "  " + "-" * 78,
    ])
    for producto in productos:
        lineas.append(f"  {producto['nombre']:<15s} {producto['cantidad']:>8,} $ {producto['costo_unitario']:>10.2f} $ {producto['pvp_normal']:>10.2f} $ {producto['pvp_mayorista']:>10.2f} $ {producto['pvp_especial']:>10.2f}")
    
    lineas.extend([
        "  " + "-" * 78,
        f"  {'TOTALES:':<15s} {cantidad_total:>8,} {'':>12s} $ {pvp_normal_total:>10.2f} $ {pvp_mayorista_total:>10.2f} $ {pvp_especial_total:>10.2f}",
        "=" * 60, "", "=" * 72, "   CONTROL DE PRORRATEO", "=" * 72,
    ])
    for nombre_gasto, criterio, monto_ingresado in gastos_contenedor:
        monto_repartido = sum((p["gastos"][nombre_gasto] for p in productos), CERO)
        lineas.append(f"   {nombre_gasto} ({criterio}): {formato_dinero(monto_ingresado)} ingresados / {formato_dinero(monto_repartido)} repartidos")
    return "\n".join(lineas) + "\n"

def inicializar_estado():
    if "config_empresa" not in st.session_state:
        st.session_state.config_empresa = dict(DEFAULTS)

def panel_configuracion():
    st.sidebar.header("⚙️ Configuración de Empresa y Origen")
    editar = st.sidebar.checkbox("Modificar datos de la empresa, proveedor y márgenes", value=False)
    config = st.session_state.config_empresa.copy()

    if editar:
        config["empresa"] = st.sidebar.text_input("Nombre de la empresa", value=config["empresa"])
        config["rif"] = st.sidebar.text_input("RIF", value=config["rif"])
        config["propietario"] = st.sidebar.text_input("Propietario", value=config["propietario"])
        config["margen"] = st.sidebar.number_input("Margen normal (%)", min_value=0.0, max_value=99.0, value=float(config["margen"]), step=0.5)
        config["desc_mayorista"] = st.sidebar.number_input("Descuento mayorista (%)", min_value=0.0, max_value=99.0, value=float(config["desc_mayorista"]), step=0.5)
        config["desc_especial"] = st.sidebar.number_input("Descuento especial (%)", min_value=0.0, max_value=99.0, value=float(config["desc_especial"]), step=0.5)
    else:
        # El recuadro azul con la info completa (Empresa + Origen)
        info_texto = (
            f"**{config['empresa']}**\n\n"
            f"RIF: {config['rif']}\n\n"
            f"**--- Datos del Origen ---**\n\n"
            f"Origen: {config.get('origen', 'No definido')}\n\n"
            f"Proveedor: {config.get('proveedor', 'No definido')}\n\n"
            f"Factura N°: {config.get('factura', 'No definido')}\n\n"
            f"**--- Márgenes ---**\n\n"
            f"Normal: {config['margen']}% · "
            f"Mayorista: {config['desc_mayorista']}% · "
            f"Especial: {config['desc_especial']}%"
        )
        st.sidebar.info(info_texto)

    # --- CAMPOS DE ORIGEN (SIEMPRE VISIBLES) ---
    st.sidebar.markdown("### 🌍 Datos de Origen")
    config["origen"] = st.sidebar.text_input("Origen (País)", value=config.get("origen", ""))
    config["proveedor"] = st.sidebar.text_input("Proveedor", value=config.get("proveedor", ""))
    config["factura"] = st.sidebar.text_input("Nro. de Factura", value=config.get("factura", ""))

    # --- NUEVO CAMPO DE FECHA ---
    fecha_actual = config.get("fecha_proximo_pedido")
    config["fecha_proximo_pedido"] = st.sidebar.date_input(
        "Fecha estimada del próximo pedido", 
        value=fecha_actual
    )
    
    # Guardar cambios en el estado de la sesión para que no se borren
    st.session_state.config_empresa = config

    return config

def leer_excel(archivo):
    if archivo.name.lower().endswith(".csv"):
        return pd.read_csv(archivo)
    return pd.read_excel(archivo)

def sugerir_columna(columnas, posibles):
    columnas_lower = {c: str(c).lower() for c in columnas}
    for palabra in posibles:
        for col, col_lower in columnas_lower.items():
            if palabra in col_lower:
                return col
    return None

def mapear_columnas(df):
    columnas = ["(ninguna)"] + list(df.columns)
    st.markdown("**Mapeo de columnas**")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c7, c8, c9 = st.columns(3)
    
    sugerencias = {
        "producto": ["producto", "descripcion", "descripción", "nombre", "articulo"],
        "cantidad": ["cantidad", "cant", "unidades", "qty"],
        "precio": ["precio", "china", "unitario", "costo", "fob"],
        "peso": ["peso", "kg", "weight"],
        "volumen": ["volumen", "m3", "cbm", "volume"],
        "stock": ["stock", "inventario", "existencia"],
        "ventas": ["venta", "ventas", "semanal", "salida"],
        "dias": ["dias", "días", "entrega", "llegada", "transito"]
    }
    
    def selector(col, etiqueta, keys):
        sug = sugerir_columna(df.columns, keys)
        idx = columnas.index(sug) if sug in columnas else 0
        return col.selectbox(etiqueta, columnas, index=idx)
        
    return {
        "producto": selector(c1, "Producto / Descripción", sugerencias["producto"]),
        "cantidad": selector(c2, "Cantidad", sugerencias["cantidad"]),
        "precio": selector(c3, "Precio en China", sugerencias["precio"]),
        "peso": selector(c4, "Peso unitario (kg)", sugerencias["peso"]),
        "volumen": selector(c5, "Volumen unitario (m³)", sugerencias["volumen"]),
        "stock": selector(c6, "Stock Actual", sugerencias["stock"]),
        "ventas": selector(c7, "Ventas Semanales", sugerencias["ventas"]),
        "dias": selector(c8, "Días de Entrega", sugerencias["dias"]),
    }

def construir_productos_desde_df(df, mapeo):
    faltantes = [k for k, v in mapeo.items() if v == "(ninguna)"]
    if faltantes:
        raise ValueError(f"Falta mapear: {', '.join(faltantes)}")
    productos = []
    for i, fila in df.iterrows():
        try:
            nombre = str(fila[mapeo["producto"]]).strip()
            cantidad = int(fila[mapeo["cantidad"
