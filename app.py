import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image
import plotly.express as px

# --- IDENTIDAD ---
EMPRESA = "M&O MEDICAL SERVICE C.A"
RIF_E = "J-507007383"
LOGO = "WhatsApp Image 2026-03-20 at 21.44.39.jpeg"

st.set_page_config(page_title=EMPRESA, layout="wide", page_icon="🏥")

# --- CONEXIÓN SEGURA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer(h):
    try:
        # ttl=0 obliga a leer datos frescos de la nube
        return conn.read(worksheet=h, ttl=0).dropna(how='all')
    except:
        return pd.DataFrame()

def guardar_seguro(df_nuevo, hoja):
    try:
        # Leemos lo que ya hay para no borrar nada
        df_actual = leer(hoja)
        # Combinamos asegurando que las columnas coincidan
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
        # Limpiamos duplicados si los hubiera por error de re-envío
        df_final = df_final.drop_duplicates().reset_index(drop=True)
        # Guardado directo
        conn.update(worksheet=hoja, data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error crítico de sincronización: {e}")
        return False

def procesar_foto(archivo):
    if archivo:
        img = Image.open(archivo).convert("RGB")
        img.thumbnail((400, 400))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=60)
        return base64.b64encode(buf.getvalue()).decode()
    return ""

# --- LOGIN ---
if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
        if st.button("Entrar"):
            # Acceso Maestro siempre disponible
            if u == "admin" and p == "MO2026":
                st.session_state.update({'rol':'admin','u_nom':'Admin Maestro','perms':["Dashboard","Inventario","Ventas","Gastos","Informes","Usuarios"]})
                st.rerun()
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                m = df_u[(df_u['Usuario'].astype(str).str.strip()==u.strip()) & (df_u['Password'].astype(str).str.strip()==p.strip())]
                if not m.empty:
                    st.session_state.update({'rol':m.iloc[0]['Rol'],'u_nom':u,'perms':["Dashboard","Inventario","Ventas","Gastos","Informes","Usuarios"] if m.iloc[0]['Rol']=='admin' else str(m.iloc[0]['Permisos']).split(',')})
                    st.rerun()
            st.error("Credenciales incorrectas")
    else:
        st.write(f"👤 **{st.session_state.u_nom}**")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- NAVEGACIÓN ---
if st.session_state.rol != 'visitante':
    menu = st.sidebar.selectbox("Sección:", st.session_state.perms)

    if menu == "Dashboard":
        st.header("📊 Dashboard de Control")
        inv, vnt, gas = leer("inventario"), leer("ventas"), leer("gastos")
        c1, c2, c3 = st.columns(3)
        if not inv.empty:
            st.metric("Equipos en Stock", len(inv))
            fig = px.pie(inv, names='Estatus', title='Distribución de Equipos')
            st.plotly_chart(fig)

    elif menu == "Inventario":
        st.header("📦 Inventario Médico")
        with st.expander("➕ REGISTRAR EQUIPO"):
            with st.form("f_inv", clear_on_submit=True):
                c1, c2 = st.columns(2)
                cod, prd = c1.text_input("Código"), c1.text_input("Producto")
                mar, mod = c1.text_input("Marca"), c1.text_input("Modelo")
                ser, ani = c2.text_input("Serial"), c2.number_input("Año", 1990, 2030, 2012)
                foto = st.file_uploader("📷 Foto", type=['jpg','png'])
                ps, est = st.number_input("Precio Venta $"), st.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                
                if st.form_submit_button("SINCRONIZAR"):
                    b64 = procesar_foto(foto)
                    # Creamos el DataFrame con la estructura exacta de tu Excel
                    nuevo = pd.DataFrame([{
                        "Código":cod, "Producto":prd, "Marca":mar, "Modelo":mod, "Serial":ser, "Año":ani,
                        "Precio_Sugerido":ps, "Estatus":est, "Foto":b64, "Fecha_Registro": datetime.now().strftime("%Y-%m-%d")
                    }])
                    if guardar_seguro(nuevo, "inventario"):
                        st.success("✅ Guardado en la Nube"); st.rerun()

    elif menu == "Ventas":
        st.header("💰 Registro de Ventas")
        with st.form("f_v"):
            eq, pv, ci = st.text_input("Equipo"), st.number_input("Precio Venta $"), st.number_input("Costo $")
            if st.form_submit_button("Vender"):
                nv = pd.DataFrame([{"Fecha":datetime.now().date(), "Equipo":eq, "Precio_Venta":pv, "Costo_Inversion":ci, "Utilidad_Neta":pv-ci}])
                if guardar_seguro(nv, "ventas"): st.rerun()

    elif menu == "Gastos":
        st.header("📉 Gastos Operativos")
        with st.form("f_g"):
            con, mon = st.text_input("Concepto"), st.number_input("Monto $")
            if st.form_submit_button("Registrar"):
                ng = pd.DataFrame([{"Fecha":datetime.now().date(), "Concepto":con, "Monto":mon}])
                if guardar_seguro(ng, "gastos"): st.rerun()

    elif menu == "Informes":
        st.header("📝 Informe de Servicio")
        with st.form("f_inf"):
            cli, eq, tr = st.text_input("Cliente"), st.text_input("Equipo"), st.text_area("Trabajo Realizado")
            if st.form_submit_button("Guardar Informe"):
                ni = pd.DataFrame([{"Fecha":datetime.now().date(), "Cliente":cli, "Equipo":eq, "Trabajo_Realizado":tr, "Tecnico":st.session_state.u_nom}])
                if guardar_seguro(ni, "informes"): st.rerun()

else:
    st.title(f"🏥 Vitrina {EMPRESA}")
    st.info("Inicia sesión para gestionar el sistema.")
