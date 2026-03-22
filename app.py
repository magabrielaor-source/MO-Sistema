import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURACIÓN DE IDENTIDAD ---
EMPRESA = "M&O MEDICAL SERVICE C.A"
RIF_EMPRESA = "J-507007383"
LOGO = "WhatsApp Image 2026-03-20 at 21.44.39.jpeg"

st.set_page_config(page_title=EMPRESA, layout="wide", page_icon="🏥")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer(hoja):
    try:
        return conn.read(worksheet=hoja, ttl=0).dropna(how='all')
    except Exception as e:
        st.warning(f"Aviso: La pestaña '{hoja}' está vacía o no se encuentra.")
        return pd.DataFrame()

def guardar(df, hoja):
    conn.update(worksheet=hoja, data=df)
    st.cache_data.clear()

# --- ESTILOS VISUALES ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .report-container { border: 2px solid #1e3a8a; padding: 25px; border-radius: 10px; background-color: white; color: black; }
    .header-table { width: 100%; border-bottom: 2px solid #1e3a8a; margin-bottom: 20px; }
    .card-publica { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-top: 5px solid #1e3a8a; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- MANEJO DE SESIÓN ---
if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- BARRA LATERAL ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        st.subheader("🔑 Acceso Staff")
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Iniciar Sesión"):
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                user = df_u[(df_u['Usuario'] == u) & (df_u['Password'].astype(str) == str(p))]
                if not user.empty:
                    st.session_state.rol = user.iloc[0]['Rol']
                    st.session_state.user_nom = u
                    st.session_state.perms = ["Dashboard", "Inventario", "Ventas", "Gastos", "Informes", "Usuarios", "Clientes"] if st.session_state.rol == 'administrador' else str(user.iloc[0]['Permisos']).split(',')
                    st.rerun()
            st.error("Credenciales incorrectas")
    else:
        st.write(f"👤 **{st.session_state.user_nom}** ({st.session_state.rol})")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- LÓGICA DE VISTAS ---
if st.session_state.rol in ['administrador', 'tecnico', 'vendedor']:
    choice = st.sidebar.selectbox("Panel Administrativo", st.session_state.perms)

    if choice == "Inventario":
        st.header("📦 Gestión de Inventario Codificado")
        df_inv = leer("inventario")
        
        with st.expander("➕ Registrar Equipo Nuevo"):
            with st.form("form_inv"):
                c1, c2, c3 = st.columns(3)
                cod = c1.text_input("Código (SKU)")
                prd = c1.text_input("Producto")
                mar = c1.text_input("Marca")
                mod = c1.text_input("Modelo")
                
                ser = c2.text_input("Serial")
                ani = c2.number_input("Año", 2000, 2030, 2024)
                ce = c2.number_input("Costo Ext $")
                cv = c2.number_input("Envío $")
                
                cr = c3.number_input("Reparación $")
                ps = c3.number_input("Precio Venta $")
                est = c3.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                tec = c3.text_input("Técnico Asignado")
                
                des = st.text_area("Descripción")
                
                if st.form_submit_button("Guardar en Nube"):
                    total = ce + cv + cr
                    nueva_fila = pd.DataFrame([[cod, prd, mar, mod, ser, ani, 1, ce, cv, cr, total, ps, tec, est, des, ""]], columns=df_inv.columns)
                    guardar(pd.concat([df_inv, nueva_fila], ignore_index=True), "inventario")
                    st.success("Guardado"); st.rerun()
        
        st.dataframe(df_inv, use_container_width=True)

    elif choice == "Informes":
        st.header("📝 Informe Técnico de Servicio")
        df_inf = leer("informes")
        
        with st.container():
            st.markdown(f"""
            <div class="report-container">
                <table class="header-table">
                    <tr>
                        <td>
                            <h2 style="margin:0;">{EMPRESA}</h2>
                            <p style="margin:0;">RIF: {RIF_EMPRESA}</p>
                            <p style="margin:0;">Ingeniería Biomédica y Servicios</p>
                        </td>
                        <td style="text-align:right; vertical-align:top;">
                            <p><b>FECHA:</b> {datetime.now().strftime('%d/%m/%Y')}</p>
                        </td>
                    </tr>
                </table>
            """, unsafe_allow_html=True)
            
            with st.form("form_informe"):
                c_cli, c_serv = st.columns([2, 1])
                with c_cli:
                    st.subheader("Datos del Cliente")
                    cli = st.text_input("Cliente / Institución")
                    rif = st.text_input("RIF / CI Cliente")
                    dir = st.text_input("Dirección")
                    res = st.text_input("Responsable en Sitio")
                    tel = st.text_input("Teléfono")
                
                with c_serv:
                    st.subheader("Tipo de Servicio")
                    t_s = st.selectbox("Seleccione:", ["Mantenimiento Preventivo", "Mantenimiento Correctivo", "Venta", "Instalación", "Inspección", "Otro"])
                    eq_i = st.text_input("Equipo")
                    ma_i = st.text_input("Marca")
                    mo_i = st.text_input("Modelo")
                    se_i = st.text_input("Serial")
                
                st.divider()
                falla = st.text_area("FALLA REPORTADA / MOTIVO DEL LLAMADO")
                trabajo = st.text_area("DESCRIPCIÓN DEL TRABAJO REALIZADO")
                repue = st.text_area("REPUESTOS Y/O ACCESORIOS UTILIZADOS")
                
                st.markdown("""
                <div style="display: flex; justify-content: space-around; margin-top: 40px; text-align: center;">
                    <div style="border-top: 1px solid black; width: 250px;"><br>Firma Técnico M&O</div>
                    <div style="border-top: 1px solid black; width: 250px;"><br>Sello y Firma Clínica</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.form_submit_button("💾 REGISTRAR INFORME FINAL"):
                    ni = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), cli, rif, dir, res, tel, t_s, eq_i, ma_i, mo_i, se_i, falla, trabajo, repue, st.session_state.user_nom]], columns=df_inf.columns)
                    guardar(pd.concat([df_inf, ni], ignore_index=True), "informes")
                    st.success("Informe Guardado"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

else:
    # VITRINA PÚBLICA
    st.markdown(f"<h1 style='text-align:center; color:#1e3a8a;'>VITRINA MÉDICA {EMPRESA}</h1>", unsafe_allow_html=True)
    df_v = leer("inventario")
    if not df_v.empty:
        listos = df_v[df_v['Estatus'] == 'Listo para Venta']
        cols = st.columns(3)
        for i, r in listos.iterrows():
            with cols[i % 3]:
                st.markdown(f"""<div class='card-publica'>
                <small>REF: {r['Código']}</small>
                <h3>{r['Marca']} {r['Modelo']}</h3>
                <p>{r['Producto']}</p>
                <h2 style='color:#2ecc71;'>${r['Precio_Sugerido']:,.2f}</h2>
                </div>""", unsafe_allow_html=True)
