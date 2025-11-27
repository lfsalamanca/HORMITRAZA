import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HormiTraza - Gestión de Residuos", layout="wide", page_icon="🐜")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #4CAF50; color: white; width: 100%; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (BASE DE DATOS TEMPORAL) ---
if 'ingresos' not in st.session_state:
    st.session_state.ingresos = pd.DataFrame(columns=['Fecha', 'Reciclador', 'Origen', 'Material', 'Peso_Kg'])
if 'salidas' not in st.session_state:
    st.session_state.salidas = pd.DataFrame(columns=['Fecha', 'Comprador', 'Tipo_Salida', 'Material', 'Peso_Kg'])

# --- TÍTULO ---
st.title("🐜 HormiTraza: Sistema de Trazabilidad")
st.markdown("**Asociación Hormiguitas Recicladoras** | Control de Balance de Masas")
st.markdown("---")

# --- BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.title("Menú Principal")
menu = st.sidebar.radio(
    "Seleccione Módulo:",
    ["1. Recepción (ECA)", "2. Comercialización/Salidas", "3. Balance de Masas (SUI)", "4. Conciliación (Cuentas)", "5. Generador de Informes"]
)

# ==========================================
# MÓDULO 1: RECEPCIÓN (ECA)
# ==========================================
if menu == "1. Recepción (ECA)":
    st.header("📥 Registro de Ingreso de Materiales")
    st.info("Cumplimiento Art. 2.3.2.5.2.2.1: Registro discriminado por origen y pesaje.")
    
    with st.form("form_ingreso"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_in = st.date_input("Fecha de Recepción", datetime.now())
            reciclador = st.text_input("Nombre del Reciclador / Operario")
            origen = st.selectbox("Origen del Residuo", ["Ruta Selectiva Ibagué", "Entrega Directa", "Otra Asociación", "Industria/Comercio"])
        with col2:
            material = st.selectbox("Tipo de Material", ["PET", "Cartón", "Vidrio", "Archivo", "Metales", "Plegadiza", "Plástico Flexible"])
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
            st.success(f"✅ Ingreso de {peso_in} Kg de {material} registrado.")

# ==========================================
# MÓDULO 2: SALIDAS
# ==========================================
elif menu == "2. Comercialización/Salidas":
    st.header("📤 Registro de Salidas")
    st.warning("Recuerde: Reportar ventas entre ECAs como aprovechamiento final es una práctica no autorizada.")
    
    with st.form("form_salida"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_out = st.date_input("Fecha de Salida", datetime.now())
            comprador = st.text_input("Empresa Compradora / Destino Final")
            tipo_salida = st.selectbox("Tipo de Salida", ["Venta (Aprovechamiento Efectivo)", "Rechazo (Relleno Sanitario)", "Venta a otra ECA (Comercialización)"])
        with col2:
            material_out = st.selectbox("Tipo de Material", ["PET", "Cartón", "Vidrio", "Archivo", "Metales", "Plegadiza", "Plástico Flexible"])
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
            st.success(f"✅ Salida registrada: {tipo_salida}")

# ==========================================
# MÓDULO 3: BALANCE DE MASAS (DASHBOARD)
# ==========================================
elif menu == "3. Balance de Masas (SUI)":
    st.header("⚖️ Balance de Masas (Tiempo Real)")
    
    # Cálculos simples para el dashboard visual
    if not st.session_state.ingresos.empty:
        df_in = st.session_state.ingresos.groupby('Material')['Peso_Kg'].sum().reset_index().rename(columns={'Peso_Kg': 'Entrada_Kg'})
    else:
        df_in = pd.DataFrame(columns=['Material', 'Entrada_Kg'])
        
    if not st.session_state.salidas.empty:
        df_out = st.session_state.salidas.groupby(['Material', 'Tipo_Salida'])['Peso_Kg'].sum().unstack(fill_value=0).reset_index()
        # Garantizar columnas
        for col in ["Venta (Aprovechamiento Efectivo)", "Rechazo (Relleno Sanitario)"]:
            if col not in df_out.columns: df_out[col] = 0
        df_out = df_out.rename(columns={"Venta (Aprovechamiento Efectivo)": "Aprovechado_Kg", "Rechazo (Relleno Sanitario)": "Rechazo_Kg"})
    else:
        df_out = pd.DataFrame(columns=['Material', 'Aprovechado_Kg', 'Rechazo_Kg'])

    balance = pd.merge(df_in, df_out, on='Material', how='outer').fillna(0)
    # Cálculo de stock (considerando ventas a otras ECAs como salida también)
    total_salidas_cols = [c for c in balance.columns if c not in ['Material', 'Entrada_Kg']]
    balance['Salidas_Totales'] = balance[total_salidas_cols].sum(axis=1)
    balance['Stock_Bodega'] = balance['Entrada_Kg'] - balance['Salidas_Totales']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ingresado", f"{balance['Entrada_Kg'].sum():,.0f} Kg")
    col2.metric("Total Aprovechado (Ventas)", f"{balance.get('Aprovechado_Kg', pd.Series([0])).sum():,.0f} Kg")
    col3.metric("Stock Actual", f"{balance['Stock_Bodega'].sum():,.0f} Kg")

    st.subheader("Visualización por Material")
    st.dataframe(balance[['Material', 'Entrada_Kg', 'Aprovechado_Kg', 'Rechazo_Kg', 'Stock_Bodega']].style.format("{:.1f}"), use_container_width=True)

# ==========================================
# MÓDULO 4: CONCILIACIÓN
# ==========================================
elif menu == "4. Conciliación (Cuentas)":
    st.header("🤝 Reporte de Conciliación (Cortes Quincenales)")
    st.write("Generación de documento soporte para el traslado de recursos.")
    # (Lógica simplificada igual a la anterior)
    if not st.session_state.salidas.empty:
        ventas = st.session_state.salidas[st.session_state.salidas['Tipo_Salida'] == "Venta (Aprovechamiento Efectivo)"]
        st.dataframe(ventas)
    else:
        st.info("No hay ventas registradas.")

# ==========================================
# MÓDULO 5: GENERADOR DE INFORMES (NUEVO)
# ==========================================
elif menu == "5. Generador de Informes":
    st.header("🖨️ Centro de Informes y Exportación")
    st.markdown("Configure los filtros a continuación para generar el reporte específico que necesita.")

    # --- FILTROS GLOBALES ---
    with st.expander("🔎 Filtros de Búsqueda (Fechas, Materiales, Personas)", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input("Fecha Inicio", value=datetime(datetime.now().year, 1, 1))
            fecha_fin = st.date_input("Fecha Fin", value=datetime.now())
        with col_f2:
            # Obtener listas únicas para los selectores
            materiales_unicos = pd.concat([st.session_state.ingresos['Material'], st.session_state.salidas['Material']]).unique()
            recicladores_unicos = st.session_state.ingresos['Reciclador'].unique()
            origenes_unicos = st.session_state.ingresos['Origen'].unique()

            filtro_material = st.multiselect("Filtrar por Material", options=materiales_unicos, default=materiales_unicos)
            filtro_reciclador = st.multiselect("Filtrar por Reciclador (Solo Ingresos)", options=recicladores_unicos, default=recicladores_unicos)
            filtro_origen = st.multiselect("Filtrar por Origen (Solo Ingresos)", options=origenes_unicos, default=origenes_unicos)

    # --- PROCESAMIENTO DE FILTROS ---
    # Convertir columnas de fecha a datetime.date para comparar
    df_in_filtered = st.session_state.ingresos.copy()
    df_out_filtered = st.session_state.salidas.copy()
    
    # Filtro Fecha
    df_in_filtered = df_in_filtered[
        (df_in_filtered['Fecha'].dt.date >= fecha_inicio) & 
        (df_in_filtered['Fecha'].dt.date <= fecha_fin)
    ]
    df_out_filtered = df_out_filtered[
        (df_out_filtered['Fecha'].dt.date >= fecha_inicio) & 
        (df_out_filtered['Fecha'].dt.date <= fecha_fin)
    ]

    # Filtro Material
    if filtro_material:
        df_in_filtered = df_in_filtered[df_in_filtered['Material'].isin(filtro_material)]
        df_out_filtered = df_out_filtered[df_out_filtered['Material'].isin(filtro_material)]
    
    # Filtro Reciclador y Origen (Solo aplica a Ingresos)
    if filtro_reciclador:
        df_in_filtered = df_in_filtered[df_in_filtered['Reciclador'].isin(filtro_reciclador)]
    if filtro_origen:
        df_in_filtered = df_in_filtered[df_in_filtered['Origen'].isin(filtro_origen)]

    # --- PESTAÑAS DE REPORTES ---
    tab1, tab2, tab3 = st.tabs(["📊 Balance General (Resumen)", "📥 Detalle Ingresos", "📤 Detalle Salidas"])

    with tab1:
        st.subheader(f"Balance General ({fecha_inicio} a {fecha_fin})")
        st.write("Resumen consolidado según los filtros aplicados.")
        
        # Agrupar para resumen
        resumen_in = df_in_filtered.groupby('Material')['Peso_Kg'].sum().reset_index().rename(columns={'Peso_Kg': 'Total_Entrada'})
        resumen_out = df_out_filtered.groupby('Material')['Peso_Kg'].sum().reset_index().rename(columns={'Peso_Kg': 'Total_Salida'})
        
        resumen_final = pd.merge(resumen_in, resumen_out, on='Material', how='outer').fillna(0)
        resumen_final['Diferencia_Periodo'] = resumen_final['Total_Entrada'] - resumen_final['Total_Salida']
        
        st.dataframe(resumen_final.style.format("{:.1f}"), use_container_width=True)
        
        # Botón descarga Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            resumen_final.to_excel(writer, sheet_name='Resumen', index=False)
            df_in_filtered.to_excel(writer, sheet_name='Detalle_Ingresos', index=False)
            df_out_filtered.to_excel(writer, sheet_name='Detalle_Salidas', index=False)
            
        st.download_button(
            label="💾 Descargar Informe Completo (Excel)",
            data=buffer,
            file_name=f"Balance_Hormiguitas_{fecha_inicio}_{fecha_fin}.xlsx",
            mime="application/vnd.ms-excel"
        )

    with tab2:
        st.subheader("Detalle de Ingresos")
        st.markdown(f"**Criterios:** Recicladores: {len(filtro_reciclador)} seleccionados | Orígenes: {len(filtro_origen)} seleccionados")
        st.dataframe(df_in_filtered, use_container_width=True)

    with tab3:
        st.subheader("Detalle de Salidas")
        st.dataframe(df_out_filtered, use_container_width=True)
