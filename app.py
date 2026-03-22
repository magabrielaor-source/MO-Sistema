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
        df = conn.read(worksheet=h, ttl=0)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

def guardar(df, h):
    conn.update(worksheet=h, data=df)
    st.cache_data.clear()

# --- ESTILOS ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .report-box { border: 2px solid #1e3a8a; padding: 25px; border-radius: 10px; background-color: white; color: black; }
    .card-v { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; border-top: 4px solid #1e3a8a; }
</style>
""", unsafe_allow_html=True)

if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- SIDEBAR / LOGIN ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            # Bypass de Emergencia
            if u_in == "admin" and p_in == "MO2026":
                st.session_state.rol = 'administrador'
                st.session_state.u_nom = "Admin Maestro"
                st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes", "Usuarios"]
                st.rerun()
            
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                df_u['Usuario'] = df_u['Usuario'].astype(str).str.strip()
                df_u['Password'] = df_u['Password'].astype(str).str.strip()
                match = df_u[(df_u['Usuario'] == u_in.strip()) & (df_u['Password'] == p_in.strip())]
                if not match.empty:
                    st.session_state.rol = match.iloc[0]['Rol']
                    st.session_state.u_nom = u_in
                    st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes", "Usuarios"] if st.session_state.rol == 'administrador' else str(match.iloc[0]['Permisos']).split(',')
                    st.rerun()
            st.error("Credenciales incorrectas")
    else:
        st.write(f"👤 **{st.session_state.u_nom}**")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- VISTAS ---
if st.session_state.rol != 'visitante':
    menu = st.sidebar.selectbox("Sección:", st.session_state.perms)

    if menu == "Dashboard":
        st.header("📊 Dashboard")
        inv, vnt, gas = leer("inventario"), leer("ventas"), leer("gastos")
        c1, c2, c3 = st.columns(3)
        if not inv.empty:
            inv['Costo_Total_Real'] = pd.to_numeric(inv['Costo_Total_Real'], errors='coerce').fillna(0)
            c1.metric("Inversión Stock", f"${inv['Costo_Total_Real'].sum():,.2f}")
            c2.metric("En Taller", len(inv[inv['Estatus'] == 'En Taller']))
            c3.metric("Para Venta", len(inv[inv['Estatus'] == 'Listo para Venta']))

    elif menu == "Inventario":
        st.header("📦 Inventario")
        df_inv = leer("inventario")
        with st.expander("➕ Registrar Equipo"):
            with st.form("f_inv"):
                c1, c2, c3 = st.columns(3)
                cod, prd, mar, mod = c1.text_input("Código"), c1.text_input("Producto"), c1.text_input("Marca"), c1.text_input("Modelo")
                ser, ani, ce, cv = c2.text_input("Serial"), c2.number_input("Año", 2024), c2.number_input("Costo Ext $"), c2.number_input("Envío $")
                cr, ps, est, tec = c3.number_input("Reparación $"), c3.number_input("Precio Venta $"), c3.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"]), c3.text_input("Técnico")
                des = st.text_area("Descripción")
                if st.form_submit_button("Guardar"):
                    nf = pd.DataFrame([[cod, prd, mar, mod, ser, ani, 1, ce, cv, cr, (ce+cv+cr), ps, tec, est, des, ""]], columns=df_inv.columns)
                    guardar(pd.concat([df_inv, nf], ignore_index=True), "inventario"); st.rerun()
        st.dataframe(df_inv)

    elif menu == "Ventas":
        st.header("💰 Registro de Ventas")
        df_v = leer("ventas")
        with st.form("f_v"):
            e, s, pv, ci = st.text_input("Equipo"), st.text_input("Serial"), st.number_input("Precio Venta $"), st.number_input("Costo Inversión $")
            if st.form_submit_button("Registrar"):
                nv = pd.DataFrame([[datetime.now().date(), e, s, pv, ci, (pv-ci)]], columns=df_v.columns)
                guardar(pd.concat([df_v, nv], ignore_index=True), "ventas"); st.rerun()
        st.dataframe(df_v)

    elif menu == "Gastos":
        st.header("📉 Gastos")
        df_g = leer("gastos")
        with st.form("f_g"):
            c, m = st.text_input("Concepto"), st.number_input("Monto $")
            if st.form_submit_button("Guardar"):
                ng = pd.DataFrame([[datetime.now().date(), c, m]], columns=df_g.columns)
                guardar(pd.concat([df_g, ng], ignore_index=True), "gastos"); st.rerun()
        st.table(df_g)

    elif menu == "Informes":
        st.header("📝 Informe Técnico")
        df_inf = leer("informes")
        with st.form("f_inf"):
            c1, c2 = st.columns(2)
            cli, rif, dir, res, tel = c1.text_input("Cliente"), c1.text_input("RIF"), c1.text_input("Dir"), c1.text_input("Resp"), c1.text_input("Tel")
            ts, eq, ma, mo, se = c2.selectbox("Servicio", ["Mantenimiento Preventivo", "Mantenimiento Correctivo", "Instalación"]), c2.text_input("Equipo"), c2.text_input("Marca"), c2.text_input("Modelo"), c2.text_input("Serial")
            fa, tr, re = st.text_area("Falla"), st.text_area("Trabajo"), st.text_area("Repuestos")
            if st.form_submit_button("💾 GUARDAR INFORME"):
                ni = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), cli, rif, dir, res, tel, ts, eq, ma, mo, se, fa, tr, re, st.session_state.u_nom]], columns=df_inf.columns)
                guardar(pd.concat([df_inf, ni], ignore_index=True), "informes"); st.rerun()
        st.dataframe(df_inf)

    elif menu == "Usuarios":
        st.header("👤 Gestión de Staff")
        df_u = leer("usuarios_staff")
        with st.expander("🔑 Crear Nuevo Usuario"):
            with st.form("f_user"):
                new_u = st.text_input("Nombre de Usuario")
                new_p = st.text_input("Contraseña")
                new_r = st.selectbox("Rol", ["administrador", "tecnico", "vendedor"])
                new_m = st.text_input("Permisos (Separados por coma)", "Dashboard,Inventario,Informes")
                if st.form_submit_button("Crear Usuario"):
                    nu = pd.DataFrame([[new_u, new_p, new_r, new_m]], columns=df_u.columns)
                    guardar(pd.concat([df_u, nu], ignore_index=True), "usuarios_staff"); st.rerun()
        st.dataframe(df_u)

else:
    st.title(f"🏥 Vitrina Pública {EMPRESA}")
    st.info("Inicie sesión para acceder al panel administrativo.")
