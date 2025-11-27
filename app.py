import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
import plotly.express as px
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="HormiTraza - Gestión de Residuos", layout="wide", page_icon="🐜")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #2E7D32; color: white; width: 100%; }
    h1, h2, h3 { color: #1B5E20; }
    .metric-card { background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if 'ingresos' not in st.session_state:
    st.session_state.ingresos = pd.DataFrame(columns=['Fecha', 'Reciclador', 'Origen', 'Material', 'Peso_Kg'])
if 'salidas' not in st.session_state:
    st.session_state.salidas = pd.DataFrame(columns=['Fecha', 'Comprador', 'Tipo_Salida', 'Material', 'Peso_Kg'])

# --- LISTAS DE CONFIGURACIÓN ---
# Rutas específicas solicitadas por la Asociación
LISTA_RUTAS = [
    "Ruta hotelera",
    "Ruta comercial",
    "Ruta Villa Vianey y otros",
    "Ruta Sausalito y otros",
    "Ruta la Estacion y otros",
    "Ruta el Bosque y otros",
    "Recepción Directa en ECA", # Opción extra necesaria
    "Otra Asociación" # Opción legal
]

MATERIALES = ["PET", "Cartón", "Vidrio", "Archivo", "Metales", "Plegadiza", "Plástico Flexible", "Chatarra"]

# --- TÍTULO ---
st.title("🐜 HormiTraza: Sistema de Trazabilidad")
st.markdown("**Asociación Hormiguitas Recicladoras** | Ibagué, Tolima")
st.markdown("---")

# --- MENÚ LATERAL ---
menu = st.sidebar.radio(
    "Módulos Operativos:",
    ["1. Recepción (ECA)", "2. Salidas y Ventas", "3. Balance de Masas (SUI)", "4. Cierre Mensual (Cortes)", "5. Informes Detallados"]
)

# ==========================================
# MÓDULO 1: RECEPCIÓN (ECA) - RUTAS ACTUALIZADAS
# ==========================================
if menu == "1. Recepción (ECA)":
    st.header("📥 Registro de Ingreso")
    st.info("Seleccione la ruta específica de recolección para mantener la trazabilidad por origen.")
    
    with st.form("form_ingreso"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_in = st.date_input("Fecha de Recepción", datetime.now())
            reciclador = st.text_input("Nombre del Reciclador / Operario")
            # AQUÍ ESTÁN LAS RUTAS NUEVAS
            origen = st.selectbox("Ruta de Origen", LISTA_RUTAS)
        with col2:
            material = st.selectbox("Tipo de Material", MATERIALES)
            peso_in = st.number_input("Peso Bruto (Kg)", min_value=0.1, step=0.1)
        
        if st.form_submit_button("Registrar Ingreso"):
            nuevo = pd.DataFrame([{
                'Fecha': pd.to_datetime(fecha_in),
                'Reciclador': reciclador,
                'Origen': origen,
                'Material': material,
                'Peso_Kg': peso_in
            }])
            st.session_state.ingresos = pd.concat([st.session_state.ingresos, nuevo], ignore_index=True)
            st.success(f"✅ Ingreso registrado: {peso_in} Kg de {material} desde {origen}")

# ==========================================
# MÓDULO 2: SALIDAS
# ==========================================
elif menu == "2. Salidas y Ventas":
    st.header("📤 Registro de Salidas")
    
    with st.form("form_salida"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_out = st.date_input("Fecha de Salida", datetime.now())
            comprador = st.text_input("Empresa Compradora")
            tipo = st.selectbox("Tipo Salida", ["Venta (Aprovechamiento)", "Rechazo (Relleno)", "Venta entre ECAs"])
        with col2:
            mat_out = st.selectbox("Material", MATERIALES)
            peso_out = st.number_input("Peso (Kg)", min_value=0.1, step=0.1)
            
        if st.form_submit_button("Registrar Salida"):
            nuevo = pd.DataFrame([{
                'Fecha': pd.to_datetime(fecha_out),
                'Comprador': comprador,
                'Tipo_Salida': tipo,
                'Material': mat_out,
                'Peso_Kg': peso_out
            }])
            st.session_state.salidas = pd.concat([st.session_state.salidas, nuevo], ignore_index=True)
            st.success("✅ Salida registrada correctamente.")

# ==========================================
# MÓDULO 3: BALANCE DASHBOARD
# ==========================================
elif menu == "3. Balance de Masas (SUI)":
    st.header("⚖️ Balance de Masas (Acumulado)")
    
    # Procesamiento de datos
    if not st.session_state.ingresos.empty:
        df_in = st.session_state.ingresos.groupby('Material')['Peso_Kg'].sum().reset_index().rename(columns={'Peso_Kg': 'Entrada'})
    else:
        df_in = pd.DataFrame(columns=['Material', 'Entrada'])
        
    if not st.session_state.salidas.empty:
        df_out = st.session_state.salidas.groupby(['Material', 'Tipo_Salida'])['Peso_Kg'].sum().unstack(fill_value=0).reset_index()
        # Asegurar columnas
        for c in ["Venta (Aprovechamiento)", "Rechazo (Relleno)"]:
            if c not in df_out.columns: df_out[c] = 0
        df_out = df_out.rename(columns={"Venta (Aprovechamiento)": "Ventas", "Rechazo (Relleno)": "Rechazos"})
    else:
        df_out = pd.DataFrame(columns=['Material', 'Ventas', 'Rechazos'])

    bal = pd.merge(df_in, df_out, on='Material', how='outer').fillna(0)
    # Stock = Entradas - Todas las salidas (incluyendo ventas a otras ECAs si las hubiera)
    cols_salida = [c for c in bal.columns if c != 'Material' and c != 'Entrada']
    bal['Total_Salidas'] = bal[cols_salida].sum(axis=1)
    bal['Stock'] = bal['Entrada'] - bal['Total_Salidas']
    
    # Tarjetas Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Recolectado", f"{bal['Entrada'].sum():,.0f} Kg")
    c2.metric("Ventas (Aprovechado)", f"{bal.get('Ventas', pd.Series([0])).sum():,.0f} Kg")
    c3.metric("Rechazos", f"{bal.get('Rechazos', pd.Series([0])).sum():,.0f} Kg")
    c4.metric("Stock en Bodega", f"{bal['Stock'].sum():,.0f} Kg")
    
    st.dataframe(bal[['Material', 'Entrada', 'Ventas', 'Rechazos', 'Stock']].style.format("{:.1f}"), use_container_width=True)

# ==========================================
# MÓDULO 4: CIERRE MENSUAL (LOGICA ACTUALIZADA)
# ==========================================
elif menu == "4. Cierre Mensual (Cortes)":
    st.header("🗓️ Generación de Corte Mensual")
    st.markdown("Seleccione el mes para generar el reporte de cierre (Día 1 al último día del mes).")
    
    col_y, col_m = st.columns(2)
    with col_y:
        year = st.number_input("Año", value=datetime.now().year)
    with col_m:
        month = st.selectbox("Mes", range(1, 13), index=datetime.now().month - 1)
    
    # Calcular último día del mes automáticamente
    last_day = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    st.info(f"Generando corte para el periodo: **{start_date}** al **{end_date}**")
    
    if not st.session_state.salidas.empty:
        # Filtrar solo ventas de ese mes
        mask = (st.session_state.salidas['Fecha'].dt.date >= start_date) & \
               (st.session_state.salidas['Fecha'].dt.date <= end_date) & \
               (st.session_state.salidas['Tipo_Salida'] == "Venta (Aprovechamiento)")
        
        corte_mes = st.session_state.salidas.loc[mask]
        
        if not corte_mes.empty:
            total_ton = corte_mes['Peso_Kg'].sum() / 1000
            st.success(f"✅ Total a Facturar en este corte: **{total_ton:.3f} Toneladas**")
            
            st.dataframe(corte_mes)
            
            # Botón descargar
            csv = corte_mes.to_csv(index=False)
            st.download_button(
                "📥 Descargar Corte Mensual (CSV)", 
                data=csv, 
                file_name=f"Corte_{year}_{month}_Hormiguitas.csv",
                mime="text/csv"
            )
        else:
            st.warning("No se encontraron ventas registradas en el mes seleccionado.")
    else:
        st.warning("No hay datos en el sistema.")

# ==========================================
# MÓDULO 5: INFORMES DETALLADOS
# ==========================================
elif menu == "5. Informes Detallados":
    st.header("🖨️ Centro de Informes")
    
    # Filtros
    with st.expander("🔎 Configurar Filtros", expanded=True):
        c1, c2 = st.columns(2)
        f_inicio = c1.date_input("Desde", datetime.now().replace(day=1))
        f_fin = c2.date_input("Hasta", datetime.now())
        
        # Filtros Multiples
        if not st.session_state.ingresos.empty:
            list_rutas = st.session_state.ingresos['Origen'].unique()
            list_reci = st.session_state.ingresos['Reciclador'].unique()
            
            sel_rutas = st.multiselect("Filtrar por Ruta/Origen", list_rutas, default=list_rutas)
            sel_reci = st.multiselect("Filtrar por Reciclador", list_reci, default=list_reci)
        else:
            sel_rutas, sel_reci = [], []

    # Lógica de filtrado
    df = st.session_state.ingresos.copy()
    if not df.empty:
        df = df[
            (df['Fecha'].dt.date >= f_inicio) & 
            (df['Fecha'].dt.date <= f_fin) &
            (df['Origen'].isin(sel_rutas)) &
            (df['Reciclador'].isin(sel_reci))
        ]

    # Vistas de Reporte
    t1, t2 = st.tabs(["📋 Resumen por Ruta", "👤 Detalle por Reciclador"])
    
    with t1:
        st.subheader("Tonelaje por Ruta")
        if not df.empty:
            por_ruta = df.groupby(['Origen', 'Material'])['Peso_Kg'].sum().unstack(fill_value=0)
            por_ruta['Total'] = por_ruta.sum(axis=1)
            st.dataframe(por_ruta.style.format("{:.1f}"))
            
            # Gráfica
            graf_ruta = df.groupby('Origen')['Peso_Kg'].sum().reset_index()
            fig = px.pie(graf_ruta, values='Peso_Kg', names='Origen', title="Participación por Ruta")
            st.plotly_chart(fig, use_container_width=True)
            
    with t2:
        st.subheader("Rendimiento por Reciclador")
        if not df.empty:
            por_reci = df.groupby('Reciclador')['Peso_Kg'].sum().reset_index().sort_values('Peso_Kg', ascending=False)
            st.dataframe(por_reci.style.format({"Peso_Kg": "{:.1f}"}))
            
            # Exportar para pagar
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Detalle', index=False)
                por_reci.to_excel(writer, sheet_name='Resumen_Pago', index=False)
                
            st.download_button("💾 Descargar Informe para Pagos (Excel)", buffer, file_name="Informe_Recicladores.xlsx")

