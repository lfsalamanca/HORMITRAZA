import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HormiTraza - Gestión de Residuos", layout="wide", page_icon="🐜")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (BASE DE DATOS TEMPORAL) ---
# En una versión productiva, esto se conectaría a SQL o Google Sheets.
if 'ingresos' not in st.session_state:
    st.session_state.ingresos = pd.DataFrame(columns=['Fecha', 'Reciclador', 'Origen', 'Material', 'Peso_Kg'])
if 'salidas' not in st.session_state:
    st.session_state.salidas = pd.DataFrame(columns=['Fecha', 'Comprador', 'Tipo_Salida', 'Material', 'Peso_Kg'])

# --- TÍTULO ---
st.title("🐜 HormiTraza: Sistema de Trazabilidad - Hormiguitas Recicladoras")
st.markdown("---")

# --- BARRA LATERAL (NAVEGACIÓN) ---
menu = st.sidebar.radio(
    "Módulos Operativos",
    ["1. Recepción (ECA)", "2. Comercialización/Salidas", "3. Balance de Masas (SUI)", "4. Conciliación (Cuentas)"]
)

# --- MÓDULO 1: RECEPCIÓN Y PESAJE (ENTRADA) ---
if menu == "1. Recepción (ECA)":
    st.header("📥 Registro de Ingreso de Materiales")
    st.info("Cumplimiento Art. 2.3.2.5.2.2.1: Registro discriminado por origen y pesaje.")
    
    with st.form("form_ingreso"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_in = st.date_input("Fecha de Recepción", datetime.now())
            reciclador = st.text_input("Nombre del Reciclador / Operario")
            origen = st.selectbox("Origen del Residuo", ["Ruta Selectiva Ibagué", "Entrega Directa", "Otra Asociación"])
        with col2:
            material = st.selectbox("Tipo de Material", ["PET", "Cartón", "Vidrio", "Archivo", "Metales", "Plegadiza"])
            peso_in = st.number_input("Peso Bruto (Kg)", min_value=0.1, step=0.1)
        
        submit_in = st.form_submit_button("Registrar Ingreso")
        
        if submit_in:
            nuevo_ingreso = pd.DataFrame([{
                'Fecha': pd.to_datetime(fecha_in),
                'Reciclador': reciclador,
                'Origen': origen,
                'Material': material,
                'Peso_Kg': peso_in
            }])
            st.session_state.ingresos = pd.concat([st.session_state.ingresos, nuevo_ingreso], ignore_index=True)
            st.success(f"✅ Ingreso de {peso_in} Kg de {material} registrado correctamente.")

    st.subheader("📋 Historial de Ingresos Recientes")
    st.dataframe(st.session_state.ingresos.sort_values(by='Fecha', ascending=False).head(10), use_container_width=True)

# --- MÓDULO 2: COMERCIALIZACIÓN Y SALIDAS ---
elif menu == "2. Comercialización/Salidas":
    st.header("📤 Registro de Salidas (Ventas y Rechazos)")
    st.warning("Importante: Registre los RECHAZOS para cumplir con la meta de reducción progresiva.")
    
    with st.form("form_salida"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_out = st.date_input("Fecha de Salida", datetime.now())
            comprador = st.text_input("Empresa Compradora / Destino")
            tipo_salida = st.selectbox("Tipo de Salida", ["Venta (Aprovechamiento Efectivo)", "Rechazo (Relleno Sanitario)"])
        with col2:
            material_out = st.selectbox("Tipo de Material", ["PET", "Cartón", "Vidrio", "Archivo", "Metales", "Plegadiza"])
            peso_out = st.number_input("Peso Salida (Kg)", min_value=0.1, step=0.1)
            
        submit_out = st.form_submit_button("Registrar Salida")
        
        if submit_out:
            nueva_salida = pd.DataFrame([{
                'Fecha': pd.to_datetime(fecha_out),
                'Comprador': comprador,
                'Tipo_Salida': tipo_salida,
                'Material': material_out,
                'Peso_Kg': peso_out
            }])
            st.session_state.salidas = pd.concat([st.session_state.salidas, nueva_salida], ignore_index=True)
            
            msg = "✅ Venta registrada." if "Venta" in tipo_salida else "⚠️ Rechazo registrado."
            st.success(msg)

# --- MÓDULO 3: BALANCE DE MASAS (DASHBOARD) ---
elif menu == "3. Balance de Masas (SUI)":
    st.header("⚖️ Balance de Masas (Normativa SUI)")
    st.markdown("Según **Resolución 276 de 2016, Art 5**: $Q_{entrada} = Q_{aprovechada} + Q_{rechazo} + Q_{almacenada}$")
    
    # Procesamiento de datos
    if not st.session_state.ingresos.empty:
        df_in = st.session_state.ingresos.groupby('Material')['Peso_Kg'].sum().reset_index().rename(columns={'Peso_Kg': 'Entrada_Kg'})
    else:
        df_in = pd.DataFrame(columns=['Material', 'Entrada_Kg'])
        
    if not st.session_state.salidas.empty:
        df_out = st.session_state.salidas.groupby(['Material', 'Tipo_Salida'])['Peso_Kg'].sum().unstack(fill_value=0).reset_index()
        # Asegurar columnas aunque no existan datos
        if "Venta (Aprovechamiento Efectivo)" not in df_out.columns: df_out["Venta (Aprovechamiento Efectivo)"] = 0
        if "Rechazo (Relleno Sanitario)" not in df_out.columns: df_out["Rechazo (Relleno Sanitario)"] = 0
        
        df_out = df_out.rename(columns={
            "Venta (Aprovechamiento Efectivo)": "Aprovechado_Kg",
            "Rechazo (Relleno Sanitario)": "Rechazo_Kg"
        })
    else:
        df_out = pd.DataFrame(columns=['Material', 'Aprovechado_Kg', 'Rechazo_Kg'])

    # Fusión de datos (Balance)
    balance = pd.merge(df_in, df_out, on='Material', how='outer').fillna(0)
    balance['Stock_Almacenado_Kg'] = balance['Entrada_Kg'] - (balance['Aprovechado_Kg'] + balance['Rechazo_Kg'])
    
    # KPIs Generales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Ingresado", f"{balance['Entrada_Kg'].sum():,.0f} Kg")
    col2.metric("Total Aprovechado", f"{balance['Aprovechado_Kg'].sum():,.0f} Kg", delta_color="normal")
    col3.metric("Total Rechazo", f"{balance['Rechazo_Kg'].sum():,.0f} Kg", delta_color="inverse")
    col4.metric("Stock en Bodega", f"{balance['Stock_Almacenado_Kg'].sum():,.0f} Kg")
    
    st.subheader("Detalle por Material")
    st.dataframe(balance.style.format("{:.1f}"), use_container_width=True)
    
    # Gráfica
    st.subheader("Visualización del Balance")
    if not balance.empty:
        fig = px.bar(balance, x='Material', y=['Aprovechado_Kg', 'Rechazo_Kg', 'Stock_Almacenado_Kg'], 
                     title="Distribución de Materiales en la ECA", barmode='relative')
        st.plotly_chart(fig, use_container_width=True)

# --- MÓDULO 4: CONCILIACIÓN DE CUENTAS ---
elif menu == "4. Conciliación (Cuentas)":
    st.header("🤝 Reporte para Comité de Conciliación")
    st.markdown("Generación de reporte para traslado de recursos (Cortes Quincenales).")
    
    fecha_corte = st.date_input("Seleccionar Fecha de Corte")
    
    st.markdown(f"""
    **Documento Preliminar para Prestador de No Aprovechables:**
    
    * **Fecha de Emisión:** {datetime.now().strftime('%Y-%m-%d')}
    * **Asociación:** Hormiguitas Recicladoras
    * **Objeto:** Traslado de recursos tarifa de aprovechamiento.
    """)
    
    st.info("Este reporte consolida las toneladas efectivamente aprovechadas (Ventas) para presentar en el comité mensual.")
    
    if not st.session_state.salidas.empty:
        ventas = st.session_state.salidas[st.session_state.salidas['Tipo_Salida'] == "Venta (Aprovechamiento Efectivo)"]
        total_facturar = ventas['Peso_Kg'].sum() / 1000 # A toneladas
        
        st.metric("Total a Conciliar (Toneladas)", f"{total_facturar:.3f} Ton")
        st.dataframe(ventas)
        
        st.download_button("Descargar Reporte Excel", data=ventas.to_csv(index=False), file_name="corte_conciliacion.csv", mime="text/csv")
    else:
        st.warning("No hay ventas registradas para generar el reporte.")
