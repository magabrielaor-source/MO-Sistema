import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURACIÓN DE IDENTIDAD ---
EMPRESA = "M&O MEDICAL SERVICE C.A"
RIF = "J-507007383"
FILENAME_LOGO = "WhatsApp Image 2026-03-20 at 21.44.39.jpeg"

# --- 2. INICIALIZACIÓN DE ARCHIVOS ---
def inicializar_archivos():
    if not os.path.exists('fotos_equipos'): os.makedirs('fotos_equipos')
    config = {
        'inventario.csv': ['Producto', 'Marca', 'Modelo', 'Serial', 'Año', 'Costo_Total_Real', 'Precio_Sugerido', 'Estatus', 'Foto'],
        'ventas.csv': ['Fecha', 'Equipo', 'Serial', 'Precio_Venta', 'Costo_Inversion', 'Utilidad_Neta'],
        'gastos.csv': ['Fecha', 'Concepto', 'Monto'],
        'informes.csv': ['Fecha', 'Equipo', 'Serial', 'Cliente', 'Procedimiento', 'Prox_Mant'],
        'clientes.csv': ['Fecha_Reg', 'Empresa', 'Nombre', 'Apellido', 'Profesion', 'Correo', 'WhatsApp', 'Password'],
        'usuarios_staff.csv': ['Usuario', 'Password', 'Rol', 'Permisos']
    }
    for nombre, columnas in config.items():
        if not os.path.exists(nombre):
            df = pd.DataFrame(columns=columnas)
            if nombre == 'usuarios_staff.csv':
                df = pd.DataFrame([["admin", "MO2026", "administrador", "Dashboard,Inventario,Ventas,Gastos,Informes,Usuarios,Clientes"]], columns=columnas)
            df.to_csv(nombre, index=False)
        else:
            df = pd.read_csv(nombre)
            for col in columnas:
                if col not in df.columns: df[col] = 0
            df.to_csv(nombre, index=False)

inicializar_archivos()

# --- 3. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title=EMPRESA, layout="wide", page_icon="🏥")

st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .card-admin { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 5px solid #1e3a8a; }
    .card-publica { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-top: 5px solid #1e3a8a; text-align: center; margin-bottom: 20px; }
    .precio-tag { color: #2ecc71; font-size: 1.5rem; font-weight: bold; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- 4. MANEJO DE SESIÓN ---
if 'user_rol' not in st.session_state: st.session_state['user_rol'] = 'visitante'
if 'user_permisos' not in st.session_state: st.session_state['user_permisos'] = []
if 'user_email' not in st.session_state: st.session_state['user_email'] = None

# --- 5. BARRA LATERAL ---
with st.sidebar:
    if os.path.exists(FILENAME_LOGO): st.image(FILENAME_LOGO, use_container_width=True)
    st.markdown(f"<div style='text-align:center;'><b>{EMPRESA}</b><br><small>{RIF}</small></div>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state['user_rol'] in ['visitante', 'registro_cliente']:
        st.subheader("🔑 Acceso Usuarios / Staff")
        u_log = st.text_input("Usuario / Correo")
        p_log = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            df_staff = pd.read_csv('usuarios_staff.csv')
            staff_match = df_staff[(df_staff['Usuario'] == u_log) & (df_staff['Password'] == str(p_log))]
            if not staff_match.empty:
                rol = staff_match.iloc[0]['Rol']
                # Fuerza permisos totales si es administrador
                if rol == "administrador":
                    permisos = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes", "Usuarios", "Clientes"]
                else:
                    permisos = staff_match.iloc[0]['Permisos'].split(',')
                
                st.session_state.update({'user_rol': rol, 'user_email': u_log, 'user_permisos': permisos})
                st.rerun()
            else:
                df_c = pd.read_csv('clientes.csv')
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

# --- 6. LÓGICA DE VISTAS ---

if st.session_state['user_rol'] == 'registro_cliente':
    st.title("📝 Registro de Cliente Nuevo")
    with st.form("reg_full"):
        c1, c2 = st.columns(2)
        n, a = c1.text_input("Nombre*"), c1.text_input("Apellido*")
        e, p = c1.text_input("Empresa"), c2.text_input("Profesión*")
        m, w = c2.text_input("Correo*"), c2.text_input("WhatsApp*")
        pw = st.text_input("Contraseña*", type="password")
        if st.form_submit_button("Registrar"):
            df_cl = pd.read_csv('clientes.csv')
            pd.concat([df_cl, pd.DataFrame([[datetime.now().date(), e, n, a, p, m, w, pw]], columns=df_cl.columns)], ignore_index=True).to_csv('clientes.csv', index=False)
            st.success("Cuenta creada."); st.session_state['user_rol'] = 'visitante'; st.rerun()
    if st.button("Volver"): st.session_state['user_rol'] = 'visitante'; st.rerun()

elif st.session_state['user_rol'] in ['administrador', 'vendedor', 'tecnico', 'staff']:
    choice = st.sidebar.selectbox("Panel Administrativo:", st.session_state['user_permisos'])
    
    if choice == "Dashboard":
        st.title("📊 Resumen Ejecutivo")
        v, g, inv = pd.read_csv('ventas.csv'), pd.read_csv('gastos.csv'), pd.read_csv('inventario.csv')
        util = (v['Utilidad_Neta'].sum() if not v.empty else 0) - (g['Monto'].sum() if not g.empty else 0)
        c1, c2, c3 = st.columns(3)
        c1.metric("Utilidad Neta Real", f"${util:,.2f}")
        c2.metric("En Taller", len(inv[inv['Estatus'] == "En Taller"]))
        c3.metric("Listo para Venta", len(inv[inv['Estatus'] == "Listo para Venta"]))

    elif choice == "Inventario":
        st.title("📦 Gestión de Inventario")
        if 'ed_i' not in st.session_state: st.session_state['ed_i'] = None
        df_inv = pd.read_csv('inventario.csv')
        with st.expander("📝 Formulario Equipo", expanded=(st.session_state['ed_i'] is not None)):
            with st.form("f_inv"):
                row = df_inv.iloc[st.session_state['ed_i']].to_dict() if st.session_state['ed_i'] is not None else {}
                c1, c2 = st.columns(2)
                p, m, mo, ser = c1.text_input("Producto", row.get('Producto',"")), c1.text_input("Marca", row.get('Marca',"")), c1.text_input("Modelo", row.get('Modelo',"")), c1.text_input("Serial", row.get('Serial',""))
                ce, ps = c2.number_input("Costo $", value=float(row.get('Costo_Total_Real',0))), c2.number_input("Sugerido $", value=float(row.get('Precio_Sugerido',0)))
                es = c2.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                fo = st.file_uploader("Foto")
                if st.form_submit_button("Guardar"):
                    ruta = row.get('Foto', "No disponible")
                    if fo:
                        ruta = os.path.join('fotos_equipos', fo.name)
                        with open(ruta, "wb") as f: f.write(fo.getbuffer())
                    new = [p, m, mo, ser, 2024, ce, ps, es, ruta]
                    if st.session_state['ed_i'] is not None: df_inv.iloc[st.session_state['ed_i']] = new
                    else: df_inv = pd.concat([df_inv, pd.DataFrame([new], columns=df_inv.columns)], ignore_index=True)
                    df_inv.to_csv('inventario.csv', index=False); st.session_state['ed_i'] = None; st.rerun()
        for i, r in df_inv.iterrows():
            st.markdown("<div class='card-admin'>", unsafe_allow_html=True)
            ci, ct, cb = st.columns([1, 3, 1])
            if r['Foto'] != "No disponible" and os.path.exists(str(r['Foto'])): ci.image(r['Foto'], use_container_width=True)
            ct.write(f"### {r['Marca']} {r['Modelo']} - {r['Estatus']}")
            if cb.button("✏️", key=f"ed_{i}"): st.session_state['ed_i'] = i; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    elif choice == "Gastos":
        st.title("📉 Gastos Operativos")
        with st.form("f_g"):
            con, mon = st.text_input("Concepto"), st.number_input("Monto $", min_value=0.0)
            if st.form_submit_button("Guardar Gasto"):
                df_g = pd.read_csv('gastos.csv')
                pd.concat([df_g, pd.DataFrame([[datetime.now().date(), con, mon]], columns=df_g.columns)], ignore_index=True).to_csv('gastos.csv', index=False); st.rerun()
        st.table(pd.read_csv('gastos.csv'))

    elif choice == "Informes":
        st.title("📝 Informes Técnicos")
        with st.expander("🆕 Nuevo Informe"):
            with st.form("f_inf"):
                c1, c2 = st.columns(2)
                e, s, cl = c1.text_input("Equipo"), c1.text_input("Serial"), c1.text_input("Cliente")
                p, pm = c2.text_area("Trabajo"), c2.date_input("Próxima Cita")
                if st.form_submit_button("Registrar"):
                    df_inf = pd.read_csv('informes.csv')
                    pd.concat([df_inf, pd.DataFrame([[datetime.now().date(), e, s, cl, p, pm]], columns=df_inf.columns)], ignore_index=True).to_csv('informes.csv', index=False); st.rerun()
        st.dataframe(pd.read_csv('informes.csv'), use_container_width=True)

    elif choice == "Usuarios":
        st.title("👥 Gestión Staff")
        df_u = pd.read_csv('usuarios_staff.csv')
        with st.form("new_u"):
            un, up, ur = st.text_input("Nombre"), st.text_input("Clave"), st.selectbox("Rol", ["administrador", "tecnico", "vendedor"])
            perms = st.multiselect("Permisos", ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes", "Usuarios", "Clientes"])
            if st.form_submit_button("Crear"):
                pd.concat([df_u, pd.DataFrame([[un, up, ur, ",".join(perms)]], columns=df_u.columns)], ignore_index=True).to_csv('usuarios_staff.csv', index=False); st.rerun()
        st.dataframe(df_u)

    elif choice == "Clientes":
        st.title("👥 Base Clientes")
        df_cl = pd.read_csv('clientes.csv')
        st.dataframe(df_cl)
        st.download_button("📥 Exportar CSV", df_cl.to_csv(index=False).encode('utf-8'), "clientes.csv", "text/csv")

    elif choice == "Ventas":
        st.title("💰 Procesar Venta")
        inv = pd.read_csv('inventario.csv')
        listos = inv[inv['Estatus'] == "Listo para Venta"]
        if listos.empty: st.warning("Sin equipos listos.")
        else:
            for idx, r in listos.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 1])
                    if r['Foto'] != "No disponible": c1.image(r['Foto'], width=150)
                    c2.write(f"**{r['Marca']} {r['Modelo']}** (S/N: {r['Serial']})")
                    if c3.button("Cerrar Venta", key=f"v_{idx}"):
                        st.session_state['v_sn_in'] = r['Serial']
                st.divider()
            if 'v_sn_in' in st.session_state:
                dat = listos[listos['Serial'] == st.session_state['v_sn_in']].iloc[0]
                with st.form("f_v_p"):
                    pf = st.number_input("Precio Final $", value=float(dat['Precio_Sugerido']))
                    if st.form_submit_button("Confirmar"):
                        gan = pf - dat['Costo_Total_Real']
                        v_df = pd.read_csv('ventas.csv')
                        pd.concat([v_df, pd.DataFrame([[datetime.now().date(), f"{dat['Marca']} {dat['Modelo']}", dat['Serial'], pf, dat['Costo_Total_Real'], gan]], columns=v_df.columns)], ignore_index=True).to_csv('ventas.csv', index=False)
                        inv.loc[inv['Serial'] == st.session_state['v_sn_in'], 'Estatus'] = "Vendido"
                        inv.to_csv('inventario.csv', index=False); del st.session_state['v_sn_in']; st.rerun()

else:
    st.markdown(f"<h1 style='text-align:center; color:#1e3a8a;'>VITRINA MÉDICA M&O</h1>", unsafe_allow_html=True)
    inv = pd.read_csv('inventario.csv')
    listos = inv[inv['Estatus'] == "Listo para Venta"]
    if listos.empty: st.info("Próximamente más equipos.")
    else:
        cols = st.columns(3)
        for idx, (_, r) in enumerate(listos.iterrows()):
            with cols[idx % 3]:
                st.markdown("<div class='card-publica'>", unsafe_allow_html=True)
                if r['Foto'] != "No disponible" and os.path.exists(str(r['Foto'])): st.image(r['Foto'], use_container_width=True)
                st.subheader(f"{r['Marca']} {r['Modelo']}")
                st.markdown(f"<div class='precio-tag'>${r['Precio_Sugerido']:,.2f}</div>", unsafe_allow_html=True)
                if st.session_state['user_rol'] == 'cliente':
                    if st.button("🛒 Consultar", key=f"pub_{idx}"): st.success("Ingeniero notificado.")
                else: st.info("Inicia sesión para adquirir")
                st.markdown("</div>", unsafe_allow_html=True)