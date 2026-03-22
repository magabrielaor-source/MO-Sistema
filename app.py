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
    .card-v { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; border-top: 4px solid #1e3a8a; }
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

# --- VISTAS ADMINISTRATIVAS ---
if st.session_state.rol in ['administrador', 'tecnico', 'vendedor']:
    menu = st.sidebar.selectbox("Seleccione Sección:", st.session_state.perms)

    if menu == "Dashboard":
        st.header("📊 Resumen de Negocio")
        inv = leer("inventario")
        gas = leer("gastos")
        if not inv.empty:
            c1, c2, c3 = st.columns(3)
            inv['Costo_Total_Real'] = pd.to_numeric(inv['Costo_Total_Real'], errors='coerce').fillna(0)
            c1.metric("Inversión Total", f"${inv['Costo_Total_Real'].sum():,.2f}")
            c2.metric("Equipos en Taller", len(inv[inv['Estatus'] == 'En Taller']))
            c3.metric("Equipos Disponibles", len(inv[inv['Estatus'] == 'Listo para Venta']))

    elif menu == "Inventario":
        st.header("📦 Inventario Codificado")
        df_inv = leer("inventario")
        with st.expander("➕ Registrar Nuevo Equipo"):
            with st.form("f_inv"):
                c1, c2, c3 = st.columns(3)
                cod, prd, mar, mod = c1.text_input("Código"), c1.text_input("Producto"), c1.text_input("Marca"), c1.text_input("Modelo")
                ser, ani, ce, cv = c2.text_input("Serial"), c2.number_input("Año", 2000, 2030, 2024), c2.number_input("Costo Ext $"), c2.number_input("Envío $")
                cr, ps, est, tec = c3.number_input("Reparación $"), c3.number_input("Precio Venta $"), c3.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"]), c3.text_input("Técnico")
                des = st.text_area("Descripción")
                if st.form_submit_button("Guardar Equipo"):
                    tot = ce + cv + cr
                    nf = pd.DataFrame([[cod, prd, mar, mod, ser, ani, 1, ce, cv, cr, tot, ps, tec, est, des, ""]], columns=df_inv.columns)
                    guardar(pd.concat([df_inv, nf], ignore_index=True), "inventario"); st.rerun()
        st.dataframe(df_inv, use_container_width=True)

    elif menu == "Ventas":
        st.header("💰 Registro de Ventas")
        df_v = leer("ventas")
        with st.form("f_v"):
            eq_v, sn_v, p_v = st.text_input("Equipo Sold"), st.text_input("Serial"), st.number_input("Precio de Venta $")
            c_v = st.number_input("Costo de Inversión (Base) $")
            if st.form_submit_button("Registrar Venta"):
                util = p_v - c_v
                nv = pd.DataFrame([[datetime.now().date(), eq_v, sn_v, p_v, c_v, util]], columns=df_v.columns)
                guardar(pd.concat([df_v, nv], ignore_index=True), "ventas"); st.rerun()
        st.dataframe(df_v)

    elif menu == "Gastos":
        st.header("📉 Egresos Operativos")
        df_g = leer("gastos")
        with st.form("f_g"):
            con_g, mon_g = st.text_input("Concepto de Gasto"), st.number_input("Monto $")
            if st.form_submit_button("Guardar Gasto"):
                ng = pd.DataFrame([[datetime.now().date(), con_g, mon_g]], columns=df_g.columns)
                guardar(pd.concat([df_g, ng], ignore_index=True), "gastos"); st.rerun()
        st.table(df_g)

    elif menu == "Informes":
        st.header("📝 Orden de Servicio Técnico")
        df_inf = leer("informes")
        st.markdown(f'<div class="report-box"><h3>{EMPRESA}</h3><p>RIF: {RIF_E}</p><p align="right">FECHA: {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)
        with st.form("f_inf"):
            c1, c2 = st.columns([2, 1])
            with c1:
                cli, r_c, d_c, res, tel = st.text_input("Cliente"), st.text_input("RIF Cliente"), st.text_input("Dirección"), st.text_input("Responsable"), st.text_input("Teléfono")
            with c2:
                t_s = st.selectbox("Tipo de Servicio", ["Mantenimiento Preventivo", "Mantenimiento Correctivo", "Instalación", "Inspección", "Venta", "Otro"])
                eq, ma, mo, se = st.text_input("Equipo"), st.text_input("Marca"), st.text_input("Modelo"), st.text_input("Serial")
            fa, tr, re = st.text_area("Falla Reportada"), st.text_area("Trabajo Realizado"), st.text_area("Repuestos/Accesorios")
            st.markdown('<div style="display:flex; justify-content:space-around; margin-top:20px;"><p>__________________<br>Firma Técnico</p><p>__________________<br>Firma Cliente</p></div>', unsafe_allow_html=True)
            if st.form_submit_button("💾 REGISTRAR INFORME FINAL"):
                ni = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), cli, r_c, d_c, res, tel, t_s, eq, ma, mo, se, fa, tr, re, st.session_state.u_nom]], columns=df_inf.columns)
                guardar(pd.concat([df_inf, ni], ignore_index=True), "informes"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.dataframe(df_inf)

else:
    # VITRINA PÚBLICA
    st.title(f"🏥 Vitrina Médica {EMPRESA}")
    inv = leer("inventario")
    if not inv.empty:
        listos = inv[inv['Estatus'] == 'Listo para Venta']
        if listos.empty: st.info("Próximamente nuevos equipos.")
        else:
            cols = st.columns(3)
            for i, r in listos.iterrows():
                with cols[i % 3]:
                    st.markdown(f"<div class='card-v'><small>REF: {r['Código']}</small><h3>{r['Marca']} {r['Modelo']}</h3><p>{r['Producto']}</p><h2 style='color:#2ecc71;'>${r['Precio_Sugerido']:,.2f}</h2></div>", unsafe_allow_html=True)
