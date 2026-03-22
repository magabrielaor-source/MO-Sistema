import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE IDENTIDAD ---
EMPRESA = "M&O MEDICAL SERVICE C.A"
RIF_E = "J-507007383"
LOGO = "WhatsApp Image 2026-03-20 at 21.44.39.jpeg"

st.set_page_config(page_title=EMPRESA, layout="wide", page_icon="🏥")

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer(h):
    try:
        # Intentamos leer la hoja
        df = conn.read(worksheet=h, ttl=0)
        return df.dropna(how='all')
    except Exception as e:
        # Si hay error, devolvemos un DataFrame vacío pero registramos el error
        return pd.DataFrame()

def guardar(df, h):
    conn.update(worksheet=h, data=df)
    st.cache_data.clear()

# --- ESTILOS ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .report-box { border: 2px solid #1e3a8a; padding: 25px; border-radius: 10px; background-color: white; color: black; }
</style>
""", unsafe_allow_html=True)

if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- BARRA LATERAL (LOGIN) ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    
    if st.session_state.rol == 'visitante':
        st.subheader("🔑 Acceso Staff")
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        
        if st.button("Iniciar Sesión"):
            # 1. ACCESO DE EMERGENCIA (Si Google Sheets falla)
            if u == "admin" and p == "MO2026":
                st.session_state.rol = 'administrador'
                st.session_state.u_nom = "Admin Maestro"
                st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes"]
                st.success("Entrando por Modo de Emergencia...")
                st.rerun()
            
            # 2. ACCESO NORMAL POR GOOGLE SHEETS
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                # Limpiamos los datos para comparar sin errores de espacios o tipos
                df_u['Usuario'] = df_u['Usuario'].astype(str).str.strip()
                df_u['Password'] = df_u['Password'].astype(str).str.strip()
                
                user = df_u[(df_u['Usuario'] == str(u).strip()) & (df_u['Password'] == str(p).strip())]
                
                if not user.empty:
                    st.session_state.rol = user.iloc[0]['Rol']
                    st.session_state.u_nom = u
                    st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes"] if st.session_state.rol == 'administrador' else str(user.iloc[0]['Permisos']).split(',')
                    st.rerun()
                else:
                    st.error("Usuario o clave no encontrados en la base de datos.")
            else:
                st.error("No se pudo conectar con la tabla de usuarios.")
    else:
        st.write(f"👤 **{st.session_state.u_nom}**")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- NAVEGACIÓN (Solo si ya ingresó) ---
if st.session_state.rol != 'visitante':
    menu = st.sidebar.selectbox("Ir a:", st.session_state.perms)

    if menu == "Dashboard":
        st.header("📊 Dashboard Financiero")
        inv = leer("inventario")
        if not inv.empty:
            st.write("Datos conectados correctamente.")
            st.metric("Total Equipos", len(inv))
        else:
            st.warning("No hay datos en la pestaña 'inventario'.")

    elif menu == "Inventario":
        st.header("📦 Inventario")
        df_inv = leer("inventario")
        # Aquí iría el formulario que ya tienes...
        st.dataframe(df_inv)

    elif menu == "Informes":
        st.header("📝 Informes")
        df_inf = leer("informes")
        # Aquí iría el formulario detallado...
        st.dataframe(df_inf)

else:
    st.title(f"🏥 Vitrina Médica {EMPRESA}")
    st.info("Inicia sesión para gestionar el sistema.")
