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

def procesar_foto(archivo):
    if archivo:
        img = Image.open(archivo).convert("RGB")
        img.thumbnail((300, 300))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=50)
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

# --- VISTAS ---
if st.session_state.rol != 'visitante':
    menu = st.sidebar.selectbox("Ir a:", st.session_state.perms)

    if menu == "Dashboard":
        st.header("📊 Resumen de Negocio")
        inv, vnt, gas = leer("inventario"), leer("ventas"), leer("gastos")
        c1, c2, c3 = st.columns(3)
        if not inv.empty:
            costo_stk = pd.to_numeric(inv['Costo_Total_Real'], errors='coerce').sum()
            c1.metric("Inversión Stock", f"${costo_stk:,.2f}")
            fig = px.pie(inv, names='Estatus', title='Estatus Equipos')
            st.plotly_chart(fig, use_container_width=True)
        if not gas.empty:
            c2.metric("Egresos Totales", f"${pd.to_numeric(gas['Monto'], errors='coerce').sum():,.2f}")

    elif menu == "Inventario":
        st.header("📦 Gestión de Inventario")
        df_inv = leer("inventario")
        with st.expander("➕ Registrar Equipo"):
            with st.form("f_inv", clear_on_submit=True):
                c1, c2 = st.columns(2)
                cod, prd, mar, mod = c1.text_input("Código"), c1.text_input("Producto"), c1.text_input("Marca"), c1.text_input("Modelo")
                ser, ani = c2.text_input("Serial"), c2.number_input("Año", 1990, 2030, 2012)
                foto = st.file_uploader("📷 Foto", type=['jpg','jpeg','png'])
                ce, cv, cr = st.number_input("Costo Ext $"), st.number_input("Envío $"), st.number_input("Reparación $")
                ps, est = st.number_input("Precio Venta $"), st.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                if st.form_submit_button("Sincronizar"):
                    b64 = procesar_foto(foto)
                    # USAMOS DICCIONARIO PARA EVITAR ERROR DE COLUMNAS
                    nuevo = {"Código":cod,"Producto":prd,"Marca":mar,"Modelo":mod,"Serial":ser,"Año":ani,"Costo_Total_Real":ce+cv+cr,"Precio_Sugerido":ps,"Estatus":est,"Foto":b64}
                    df_final = pd.concat([df_inv, pd.DataFrame([nuevo])], ignore_index=True)
                    guardar(df_final, "inventario")
                    st.success("✅ Guardado"); st.rerun()
        st.dataframe(df_inv)

    elif menu == "Ventas":
        st.header("💰 Registro de Ventas")
        df_v = leer("ventas")
        with st.form("fv"):
            eq, sn, pv, ci = st.text_input("Equipo"), st.text_input("Serial"), st.number_input("Venta $"), st.number_input("Costo $")
            if st.form_submit_button("Vender"):
                nv = pd.concat([df_v, pd.DataFrame([{"Fecha":datetime.now().date(),"Equipo":eq,"Serial":sn,"Precio_Venta":pv,"Costo_Inversion":ci,"Utilidad_Neta":pv-ci}])], ignore_index=True)
                guardar(nv, "ventas"); st.rerun()
        st.dataframe(df_v)

    elif menu == "Gastos":
        st.header("📉 Gastos")
        df_g = leer("gastos")
        with st.form("fg"):
            con, mon = st.text_input("Concepto"), st.number_input("Monto $")
            if st.form_submit_button("Registrar"):
                ng = pd.concat([df_g, pd.DataFrame([{"Fecha":datetime.now().date(),"Concepto":con,"Monto":mon}])], ignore_index=True)
                guardar(ng, "gastos"); st.rerun()
        st.table(df_g)

    elif menu == "Informes":
        st.header("📝 Informe de Servicio")
        df_inf = leer("informes")
        with st.form("finf"):
            cli, rif, ts, eq = st.text_input("Cliente"), st.text_input("RIF"), st.selectbox("Tipo", ["Mantenimiento", "Reparación"]), st.text_input("Equipo")
            falla, trab = st.text_area("Falla"), st.text_area("Trabajo")
            if st.form_submit_button("Guardar"):
                ni = pd.concat([df_inf, pd.DataFrame([{"Fecha":datetime.now().date(),"Cliente":cli,"RIF":rif,"Tipo_Servicio":ts,"Equipo":eq,"Falla":falla,"Trabajo_Realizado":trab,"Tecnico":st.session_state.u_nom}])], ignore_index=True)
                guardar(ni, "informes"); st.rerun()
        st.dataframe(df_inf)

    elif menu == "Usuarios":
        st.header("👤 Staff")
        df_u = leer("usuarios_staff")
        with st.form("fu"):
            nu, np = st.text_input("Usuario"), st.text_input("Clave")
            if st.form_submit_button("Crear"):
                nu_df = pd.concat([df_u, pd.DataFrame([{"Usuario":nu,"Password":np,"Rol":"tecnico","Permisos":"Dashboard,Inventario,Informes"}])], ignore_index=True)
                guardar(nu_df, "usuarios_staff"); st.rerun()
        st.dataframe(df_u)

else:
    st.title(f"🏥 Vitrina Médica {EMPRESA}")
    inv = leer("inventario")
    if not inv.empty:
        listos = inv[inv['Estatus'] == 'Listo para Venta']
        cols = st.columns(3)
        for i, r in listos.iterrows():
            with cols[i % 3]:
                st.markdown("<div style='border:1px solid #ddd; padding:10px; border-radius:10px; text-align:center;'>", unsafe_allow_html=True)
                if r['Foto']: st.image(f"data:image/jpeg;base64,{r['Foto']}", use_container_width=True)
                st.write(f"**{r['Marca']} {r['Modelo']}**")
                st.write(f"${r['Precio_Sugerido']}")
                st.markdown("</div>", unsafe_allow_html=True)
