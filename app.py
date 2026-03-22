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
    .report-box { border: 2px solid #1e3a8a; padding: 25px; border-radius: 10px; background-color: white; color: black; font-family: sans-serif; }
    .card-v { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; border-top: 4px solid #1e3a8a; }
    .metric-box { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
</style>
""", unsafe_allow_html=True)

if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Iniciar Sesión"):
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                df_u['Password'] = df_u['Password'].astype(str)
                user = df_u[(df_u['Usuario'] == u) & (df_u['Password'] == str(p))]
                if not user.empty:
                    st.session_state.rol = user.iloc[0]['Rol']
                    st.session_state.u_nom = u
                    # Permisos automáticos para admin, o personalizados para staff
                    st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes"] if st.session_state.rol == 'administrador' else str(user.iloc[0]['Permisos']).split(',')
                    st.rerun()
            st.error("Credenciales incorrectas")
    else:
        st.write(f"👤 Usuario: **{st.session_state.u_nom}**")
        st.write(f"Role: *{st.session_state.rol}*")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- VISTAS ADMINISTRATIVAS ---
if st.session_state.rol in ['administrador', 'tecnico', 'vendedor']:
    menu = st.sidebar.selectbox("Seleccione Sección:", st.session_state.perms)

    if menu == "Dashboard":
        st.header("📊 Resumen de Operaciones")
        inv = leer("inventario")
        vnt = leer("ventas")
        gas = leer("gastos")
        
        c1, c2, c3, c4 = st.columns(4)
        if not inv.empty:
            inv['Costo_Total_Real'] = pd.to_numeric(inv['Costo_Total_Real'], errors='coerce').fillna(0)
            c1.metric("Activos en Stock", f"${inv['Costo_Total_Real'].sum():,.2f}")
            c2.metric("Equipos en Taller", len(inv[inv['Estatus'] == 'En Taller']))
        
        if not vnt.empty:
            vnt['Utilidad_Neta'] = pd.to_numeric(vnt['Utilidad_Neta'], errors='coerce').fillna(0)
            c3.metric("Utilidad Bruta", f"${vnt['Utilidad_Neta'].sum():,.2f}")
            
        if not gas.empty:
            gas['Monto'] = pd.to_numeric(gas['Monto'], errors='coerce').fillna(0)
            c4.metric("Gastos Totales", f"${gas['Monto'].sum():,.2f}")

    elif menu == "Inventario":
        st.header("📦 Gestión de Inventario")
        df_inv = leer("inventario")
        with st.expander("➕ Registrar Equipo Nuevo"):
            with st.form("f_inv"):
                c1, c2, c3 = st.columns(3)
                cod = c1.text_input("Código (SKU)")
                prd = c1.text_input("Producto/Categoría")
                mar = c1.text_input("Marca")
                mod = c1.text_input("Modelo")
                
                ser = c2.text_input("Serial")
                ani = c2.number_input("Año", 2000, 2030, 2024)
                ce = c2.number_input("Costo Compra Exterior $")
                cv = c2.number_input("Envío/Aduana $")
                
                cr = c3.number_input("Inversión Reparación $")
                ps = c3.number_input("Precio Sugerido Venta $")
                est = c3.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                tec = c3.text_input("Técnico Asignado")
                
                des = st.text_area("Descripción/Observaciones")
                
                if st.form_submit_button("Guardar en Nube"):
                    total = ce + cv + cr
                    nf = pd.DataFrame([[cod, prd, mar, mod, ser, ani, 1, ce, cv, cr, total, ps, tec, est, des, ""]], columns=df_inv.columns)
                    guardar(pd.concat([df_inv, nf], ignore_index=True), "inventario")
                    st.success("Guardado"); st.rerun()
        st.dataframe(df_inv, use_container_width=True)

    elif menu == "Ventas":
        st.header("💰 Registro de Ventas")
        df_v = leer("ventas")
        with st.form("f_v"):
            c1, c2 = st.columns(2)
            eq_v = c1.text_input("Equipo Vendido")
            sn_v = c1.text_input("Serial")
            p_v = c2.number_input("Precio de Venta $")
            c_v = c2.number_input("Costo de Inversión Total $")
            if st.form_submit_button("Registrar Venta"):
                util = p_v - c_v
                nv = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), eq_v, sn_v, p_v, c_v, util]], columns=df_v.columns)
                guardar(pd.concat([df_v, nv], ignore_index=True), "ventas"); st.rerun()
        st.dataframe(df_v, use_container_width=True)

    elif menu == "Gastos":
        st.header("📉 Control de Gastos")
        df_g = leer("gastos")
        with st.form("f_g"):
            con_g = st.text_input("Concepto del Gasto")
            mon_g = st.number_input("Monto $")
            if st.form_submit_button("Guardar Gasto"):
                ng = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), con_g, mon_g]], columns=df_g.columns)
                guardar(pd.concat([df_g, ng], ignore_index=True), "gastos"); st.rerun()
        st.table(df_g)

    elif menu == "Informes":
        st.header("📝 Orden de Servicio Técnico Profesional")
        df_inf = leer("informes")
        
        st.markdown(f"""
        <div class="report-box">
            <table style="width:100%">
                <tr>
                    <td style="width:70%">
                        <h2 style="margin:0; color:#1e3a8a;">{EMPRESA}</h2>
                        <p style="margin:0;">RIF: {RIF_E}</p>
                        <p style="margin:0;">Ingeniería Biomédica y Servicios Especializados</p>
                    </td>
                    <td style="text-align:right">
                        <p><b>FECHA:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                    </td>
                </tr>
            </table>
            <hr>
        """, unsafe_allow_html=True)
        
        with st.form("f_inf"):
            c_cli, c_det = st.columns([2, 1])
            with c_cli:
                st.subheader("Datos del Cliente")
                cli = st.text_input("Cliente / Institución")
                rif_c = st.text_input("RIF / CI Cliente")
                dir_c = st.text_input("Dirección")
                res_c = st.text_input("Responsable")
                tel_c = st.text_input("Teléfono")
            
            with c_det:
                st.subheader("Detalle Servicio")
                t_s = st.selectbox("Tipo de Servicio", ["Mantenimiento Preventivo", "Mantenimiento Correctivo", "Instalación", "Inspección", "Venta", "Otro"])
                eq_n = st.text_input("Equipo")
                ma_n = st.text_input("Marca")
                mo_n = st.text_input("Modelo")
                se_n = st.text_input("Serial")
            
            st.divider()
            falla = st.text_area("FALLA REPORTADA / MOTIVO DEL LLAMADO")
            trabajo = st.text_area("DESCRIPCIÓN DEL TRABAJO REALIZADO")
            repue = st.text_area("REPUESTOS Y/O ACCESORIOS UTILIZADOS")
            
            st.markdown("""
            <div style="display:flex; justify-content:space-around; margin-top:40px; text-align:center;">
                <div style="border-top:1px solid black; width:200px;"><br>Firma Técnico M&O</div>
                <div style="border-top:1px solid black; width:200px;"><br>Firma y Sello Cliente</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.form_submit_button("💾 GUARDAR INFORME"):
                ni = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), cli, rif_c, dir_c, res_c, tel_c, t_s, eq_n, ma_n, mo_n, se_n, falla, trabajo, repue, st.session_state.u_nom]], columns=df_inf.columns)
                guardar(pd.concat([df_inf, ni], ignore_index=True), "informes"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.dataframe(df_inf, use_container_width=True)

else:
    # VITRINA PÚBLICA (LO QUE VE EL CLIENTE SIN LOGUEARSE)
    st.markdown(f"<h1 style='text-align:center; color:#1e3a8a;'>VITRINA MÉDICA {EMPRESA}</h1>", unsafe_allow_html=True)
    inv = leer("inventario")
    if not inv.empty:
        listos = inv[inv['Estatus'] == 'Listo para Venta']
        if listos.empty:
            st.info("Estamos actualizando nuestro catálogo. ¡Vuelve pronto!")
        else:
            cols = st.columns(3)
            for i, r in listos.iterrows():
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class='card-v'>
                        <small>REF: {r['Código']}</small>
                        <h3>{r['Marca']} {r['Modelo']}</h3>
                        <p>{r['Producto']}</p>
                        <h2 style='color:#2ecc71;'>${pd.to_numeric(r['Precio_Sugerido'], errors='coerce'):,.2f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
