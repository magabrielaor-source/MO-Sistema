import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
EMPRESA = "M&O MEDICAL SERVICE C.A"
RIF_E = "J-507007383"
LOGO = "WhatsApp Image 2026-03-20 at 21.44.39.jpeg"

st.set_page_config(page_title=EMPRESA, layout="wide", page_icon="🏥")

# Conexión Segura
conn = st.connection("gsheets", type=GSheetsConnection)

def leer(h):
    try:
        return conn.read(worksheet=h, ttl=0).dropna(how='all')
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
    .card-v { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
</style>
""", unsafe_allow_html=True)

if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                df_u['Password'] = df_u['Password'].astype(str)
                user = df_u[(df_u['Usuario'] == u) & (df_u['Password'] == str(p))]
                if not user.empty:
                    st.session_state.rol = user.iloc[0]['Rol']
                    st.session_state.u_nom = u
                    st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes"] if st.session_state.rol == 'administrador' else str(user.iloc[0]['Permisos']).split(',')
                    st.rerun()
            st.error("Credenciales incorrectas")
    else:
        st.write(f"👤 {st.session_state.u_nom}")
        if st.button("Salir"):
            st.session_state.clear()
            st.rerun()

# --- VISTAS ---
if st.session_state.rol in ['administrador', 'tecnico', 'vendedor']:
    menu = st.sidebar.selectbox("Menú", st.session_state.perms)

    if menu == "Inventario":
        st.header("📦 Inventario Codificado")
        df_inv = leer("inventario")
        with st.expander("➕ Registrar Equipo"):
            with st.form("f_inv"):
                c1, c2, c3 = st.columns(3)
                cod, prd, mar, mod = c1.text_input("Código"), c1.text_input("Producto"), c1.text_input("Marca"), c1.text_input("Modelo")
                ser, ani, ce, cv = c2.text_input("Serial"), c2.number_input("Año", 2024), c2.number_input("Costo Ext $"), c2.number_input("Envío $")
                cr, ps, est, tec = c3.number_input("Reparación $"), c3.number_input("Precio Venta $"), c3.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"]), c3.text_input("Técnico")
                if st.form_submit_button("Guardar"):
                    tot = ce + cv + cr
                    nf = pd.DataFrame([[cod, prd, mar, mod, ser, ani, 1, ce, cv, cr, tot, ps, tec, est, "", ""]], columns=df_inv.columns)
                    guardar(pd.concat([df_inv, nf], ignore_index=True), "inventario"); st.rerun()
        st.dataframe(df_inv)

    elif menu == "Informes":
        st.header("📝 Orden de Servicio Técnico")
        df_inf = leer("informes")
        st.markdown(f'<div class="report-box"><h3>{EMPRESA}</h3><p>RIF: {RIF_E}</p><p align="right">FECHA: {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)
        with st.form("f_inf"):
            c1, c2 = st.columns([2, 1])
            with c1:
                cli, r_c, d_c, res, tel = st.text_input("Cliente"), st.text_input("RIF Cliente"), st.text_input("Dirección"), st.text_input("Responsable"), st.text_input("Teléfono")
            with c2:
                t_s = st.selectbox("Servicio", ["Mantenimiento Preventivo", "Mantenimiento Correctivo", "Instalación", "Inspección", "Venta"])
                eq, ma, mo, se = st.text_input("Equipo"), st.text_input("Marca"), st.text_input("Modelo"), st.text_input("Serial")
            fa, tr, re = st.text_area("Falla"), st.text_area("Trabajo Realizado"), st.text_area("Repuestos")
            if st.form_submit_button("💾 REGISTRAR INFORME"):
                ni = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), cli, r_c, d_c, res, tel, t_s, eq, ma, mo, se, fa, tr, re, st.session_state.u_nom]], columns=df_inf.columns)
                guardar(pd.concat([df_inf, ni], ignore_index=True), "informes"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.title(f"🏥 Vitrina {EMPRESA}")
    inv = leer("inventario")
    if not inv.empty:
        listos = inv[inv['Estatus'] == 'Listo para Venta']
        cols = st.columns(3)
        for i, r in listos.iterrows():
            with cols[i % 3]:
                st.markdown(f"<div class='card-v'><small>{r['Código']}</small><h3>{r['Marca']} {r['Modelo']}</h3><h2 style='color:#2ecc71;'>${r['Precio_Sugerido']}</h2></div>", unsafe_allow_html=True)
