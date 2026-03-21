import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- CONFIGURACIÓN DE IDENTIDAD ---
EMPRESA = "M&O MEDICAL SERVICE C.A"
RIF = "J-507007383"
FILENAME_LOGO = "WhatsApp Image 2026-03-20 at 21.44.39.jpeg"

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestaña):
    return conn.read(worksheet=pestaña, ttl=0)

def guardar_datos(df, pestaña):
    conn.update(worksheet=pestaña, data=df)
    st.cache_data.clear()

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title=EMPRESA, layout="wide", page_icon="🏥")

st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .card-admin { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 5px solid #1e3a8a; }
    .card-publica { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-top: 5px solid #1e3a8a; text-align: center; margin-bottom: 20px; }
    .precio-tag { color: #2ecc71; font-size: 1.5rem; font-weight: bold; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- MANEJO DE SESIÓN ---
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'visitante'
if 'user_permisos' not in st.session_state: st.session_state['user_permisos'] = []
if 'user_email' not in st.session_state: st.session_state['user_email'] = None

# --- BARRA LATERAL ---
with st.sidebar:
    if os.path.exists(FILENAME_LOGO): st.image(FILENAME_LOGO, use_container_width=True)
    st.markdown(f"<div style='text-align:center;'><b>{EMPRESA}</b><br><small>{RIF}</small></div>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state['user_rol'] in ['visitante', 'registro_cliente']:
        st.subheader("🔑 Acceso Usuarios / Staff")
        u_log = st.text_input("Usuario / Correo")
        p_log = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            df_staff = leer_datos("usuarios_staff")
            staff_match = df_staff[(df_staff['Usuario'] == u_log) & (df_staff['Password'] == str(p_log))]
            if not staff_match.empty:
                rol = staff_match.iloc[0]['Rol']
                perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes", "Usuarios", "Clientes"] if rol == "administrador" else staff_match.iloc[0]['Permisos'].split(',')
                st.session_state.update({'user_rol': rol, 'user_email': u_log, 'user_permisos': perms})
                st.rerun()
            else:
                df_c = leer_datos("clientes")
                c_match = df_c[(df_c['Correo'] == u_log) & (df_c['Password'] == str(p_log))]
                if not c_match.empty:
                    st.session_state.update({'user_rol': 'cliente', 'user_email': u_log})
                    st.rerun()
                else: st.error("Credenciales incorrectas")
        
        if st.button("Crear Cuenta de Cliente"):
            st.session_state['user_rol'] = 'registro_cliente'
            st.rerun()
    else:
        st.write(f"👤 **{st.session_state['user_email']}**")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- LÓGICA DE VISTAS ---

if st.session_state['user_rol'] == 'registro_cliente':
    st.title("📝 Registro de Cliente Nuevo")
    with st.form("reg_full"):
        c1, c2 = st.columns(2)
        n, a = c1.text_input("Nombre*"), c1.text_input("Apellido*")
        e, prof = c1.text_input("Empresa"), c2.text_input("Profesión*")
        m, w = c2.text_input("Correo*"), c2.text_input("WhatsApp*")
        pw = st.text_input("Contraseña*", type="password")
        if st.form_submit_button("Registrar"):
            df_cl = leer_datos("clientes")
            pd.concat([df_cl, pd.DataFrame([[datetime.now().date(), e, n, a, prof, m, w, pw]], columns=df_cl.columns)], ignore_index=True).to_csv('clientes.csv', index=False)
            st.success("Cuenta creada."); st.session_state['user_rol'] = 'visitante'; st.rerun()

elif st.session_state['user_rol'] in ['administrador', 'vendedor', 'tecnico', 'staff']:
    choice = st.sidebar.selectbox("Panel Administrativo:", st.session_state['user_permisos'])
    
    if choice == "Dashboard":
        st.title("📊 Resumen Ejecutivo")
        v, g, inv = leer_datos("ventas"), leer_datos("gastos"), leer_datos("inventario")
        util = (v['Utilidad_Neta'].sum() if not v.empty else 0) - (g['Monto'].sum() if not g.empty else 0)
        c1, c2, c3 = st.columns(3)
        c1.metric("Utilidad Neta Real", f"${util:,.2f}")
        c2.metric("En Taller", len(inv[inv['Estatus'] == "En Taller"]))
        c3.metric("Listo para Venta", len(inv[inv['Estatus'] == "Listo para Venta"]))

    elif choice == "Inventario":
        st.title("📦 Gestión Completa de Inventario")
        if 'ed_i' not in st.session_state: st.session_state['ed_i'] = None
        df_inv = leer_datos("inventario")
        
        with st.expander("📝 Formulario Técnico de Equipo", expanded=(st.session_state['ed_i'] is not None)):
            with st.form("f_inv_completo"):
                row = df_inv.iloc[st.session_state['ed_i']].to_dict() if st.session_state['ed_i'] is not None else {}
                c1, c2, c3 = st.columns(3)
                p, m, mo = c1.text_input("Producto", row.get('Producto',"")), c1.text_input("Marca", row.get('Marca',"")), c1.text_input("Modelo", row.get('Modelo',""))
                ser, anio = c1.text_input("Serial", row.get('Serial',"")), c1.number_input("Año", value=int(row.get('Año', 2024)))
                c_ext, c_env, c_rep = c2.number_input("Costo Exterior $", value=float(row.get('Costo_Extranjero',0))), c2.number_input("Envío $", value=float(row.get('Envio_VZLA',0))), c2.number_input("Reparación $", value=float(row.get('Inversion_Reparacion',0)))
                p_sug, est = c2.number_input("Precio Sugerido $", value=float(row.get('Precio_Sugerido',0))), c3.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                tec, desc = c3.text_input("Técnico", row.get('Tecnico', "M&O")), st.text_area("Descripción", row.get('Descripcion', ""))
                if st.form_submit_button("Guardar Cambios"):
                    costo_t = c_ext + c_env + c_rep
                    new = [p, m, mo, ser, anio, 1, c_ext, c_env, c_rep, costo_t, p_sug, tec, est, desc, row.get('Foto', "No disponible")]
                    if st.session_state['ed_i'] is not None: df_inv.iloc[st.session_state['ed_i']] = new
                    else: df_inv = pd.concat([df_inv, pd.DataFrame([new], columns=df_inv.columns)], ignore_index=True)
                    guardar_datos(df_inv, "inventario"); st.session_state['ed_i'] = None; st.rerun()

        for i, r in df_inv.iterrows():
            st.markdown("<div class='card-admin'>", unsafe_allow_html=True)
            ci, ct, cb = st.columns([1, 3, 1])
            ct.write(f"### {r['Marca']} {r['Modelo']} - {r['Estatus']}")
            ct.write(f"S/N: {r['Serial']} | Inversión: ${r['Costo_Total_Real']:.2f}")
            if cb.button("✏️", key=f"ed_{i}"): st.session_state['ed_i'] = i; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    elif choice == "Gastos":
        st.title("📉 Gastos Operativos")
        df_g = leer_datos("gastos")
        with st.form("f_g"):
            con, mon = st.text_input("Concepto"), st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("Guardar Gasto"):
                pd.concat([df_g, pd.DataFrame([[datetime.now().date(), con, mon]], columns=df_g.columns)], ignore_index=True).pipe(guardar_datos, "gastos"); st.rerun()
        st.table(df_g)

    elif choice == "Informes":
        st.title("📝 Informes Técnicos")
        df_inf = leer_datos("informes")
        with st.expander("🆕 Nuevo Informe"):
            with st.form("f_inf"):
                e, s, cl = st.text_input("Equipo"), st.text_input("Serial"), st.text_input("Cliente")
                p, pm = st.text_area("Trabajo"), st.date_input("Próxima Cita")
                if st.form_submit_button("Registrar"):
                    pd.concat([df_inf, pd.DataFrame([[datetime.now().date(), e, s, cl, p, pm]], columns=df_inf.columns)], ignore_index=True).pipe(guardar_datos, "informes"); st.rerun()
        st.dataframe(df_inf, use_container_width=True)

else:
    st.markdown(f"<h1 style='text-align:center; color:#1e3a8a;'>VITRINA MÉDICA M&O</h1>", unsafe_allow_html=True)
    inv = leer_datos("inventario")
    listos = inv[inv['Estatus'] == "Listo para Venta"]
    if listos.empty: st.info("Próximamente más equipos.")
    else:
        cols = st.columns(3)
        for idx, (_, r) in enumerate(listos.iterrows()):
            with cols[idx % 3]:
                st.markdown("<div class='card-publica'>", unsafe_allow_html=True)
                st.subheader(f"{r['Marca']} {r['Modelo']}")
                st.markdown(f"<div class='precio-tag'>${r['Precio_Sugerido']:,.2f}</div>", unsafe_allow_html=True)
                if st.session_state['user_rol'] == 'cliente':
                    if st.button("🛒 Consultar", key=f"pub_{idx}"): st.success("Ingeniero notificado.")
                else: st.info("Inicia sesión para adquirir")
                st.markdown("</div>", unsafe_allow_html=True)
