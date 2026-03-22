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
    # Usamos un método de guardado más compatible para evitar el UnsupportedOperationError
    conn.update(worksheet=h, data=df)
    st.cache_data.clear()

def procesar_foto(archivo):
    if archivo:
        img = Image.open(archivo).convert("RGB")
        img.thumbnail((500, 500))
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    return ""

# --- ESTILOS ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .card-v { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #1e3a8a; margin-bottom: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- LOGIN ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
        if st.button("Entrar"):
            if u == "admin" and p == "MO2026":
                st.session_state.update({'rol':'administrador','u_nom':'Admin Maestro','perms':["Dashboard","Inventario","Ventas","Gastos","Informes","Usuarios"]})
                st.rerun()
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                m = df_u[(df_u['Usuario'].astype(str).str.strip()==u.strip()) & (df_u['Password'].astype(str).str.strip()==p.strip())]
                if not m.empty:
                    st.session_state.update({'rol':m.iloc[0]['Rol'],'u_nom':u,'perms':["Dashboard","Inventario","Ventas","Gastos","Informes","Usuarios"] if m.iloc[0]['Rol']=='administrador' else str(m.iloc[0]['Permisos']).split(',')})
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
        st.header("📊 Inteligencia de Negocios")
        inv, vnt, gas = leer("inventario"), leer("ventas"), leer("gastos")
        
        # Métricas principales
        c1, c2, c3, c4 = st.columns(4)
        total_inv = pd.to_numeric(inv['Costo_Total_Real'], errors='coerce').sum() if not inv.empty else 0
        total_vnt = pd.to_numeric(vnt['Precio_Venta'], errors='coerce').sum() if not vnt.empty else 0
        total_gas = pd.to_numeric(gas['Monto'], errors='coerce').sum() if not gas.empty else 0
        utilidad = (pd.to_numeric(vnt['Utilidad_Neta'], errors='coerce').sum() if not vnt.empty else 0) - total_gas
        
        c1.metric("Activos (Stock)", f"${total_inv:,.2f}")
        c2.metric("Ventas Totales", f"${total_vnt:,.2f}")
        c3.metric("Egresos", f"${total_gas:,.2f}")
        c4.metric("Utilidad Real", f"${utilidad:,.2f}")

        # Gráficos
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if not inv.empty:
                fig_inv = px.pie(inv, names='Estatus', title='Estado del Inventario', hole=.4)
                st.plotly_chart(fig_inv, use_container_width=True)
        with col_g2:
            if not gas.empty:
                fig_gas = px.bar(gas, x='Concepto', y='Monto', title='Distribución de Gastos', color='Monto')
                st.plotly_chart(fig_gas, use_container_width=True)

    elif menu == "Inventario":
        st.header("📦 Inventario")
        df_inv = leer("inventario")
        with st.expander("➕ Registrar Equipo"):
            with st.form("f_inv", clear_on_submit=True):
                c1, c2 = st.columns(2)
                cod, prd, mar, mod = c1.text_input("Código"), c1.text_input("Producto"), c1.text_input("Marca"), c1.text_input("Modelo")
                ser, ani = c2.text_input("Serial"), c2.number_input("Año", 1990, 2030, 2012)
                foto = st.file_uploader("📷 Foto", type=['jpg','png','jpeg'])
                ca, cb, cc = st.columns(3)
                costo_e, costo_v, costo_r = ca.number_input("Ext $"), cb.number_input("Envío $"), cc.number_input("Reparación $")
                ps, est, tec = st.number_input("Precio Venta $"), st.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"]), st.text_input("Técnico")
                des = st.text_area("Descripción")
                if st.form_submit_button("Guardar"):
                    b64 = procesar_foto(foto)
                    new = pd.DataFrame([{"Código":cod,"Producto":prd,"Marca":mar,"Modelo":mod,"Serial":ser,"Año":ani,"Cantidad":1,"Costo_Extranjero":costo_e,"Envio_VZLA":costo_v,"Inversion_Reparacion":costo_r,"Costo_Total_Real":costo_e+costo_v+costo_r,"Precio_Sugerido":ps,"Tecnico":tec,"Estatus":est,"Descripcion":des,"Foto":b64}])
                    guardar(pd.concat([df_inv, new], ignore_index=True), "inventario")
                    st.success("Sincronizado"); st.rerun()
        
        # Opción para borrar equipos (Control de Errores)
        st.subheader("Listado General")
        st.dataframe(df_inv)
        if not df_inv.empty:
            fila_borrar = st.number_input("Fila a eliminar (Índice)", min_value=0, max_value=len(df_inv)-1, step=1)
            if st.button("🗑️ Eliminar Equipo Seleccionado"):
                df_inv = df_inv.drop(fila_borrar)
                guardar(df_inv, "inventario")
                st.warning("Equipo eliminado"); st.rerun()

    elif menu == "Ventas":
        st.header("💰 Registro de Ventas")
        df_v = leer("ventas")
        with st.form("f_v"):
            c1, c2 = st.columns(2)
            eq, sn = c1.text_input("Equipo"), c1.text_input("Serial")
            pv, ci = c2.number_input("Precio Venta $"), c2.number_input("Costo Inversión $")
            if st.form_submit_button("Registrar Venta"):
                nv = pd.DataFrame([{"Fecha":datetime.now().date(),"Equipo":eq,"Serial":sn,"Precio_Venta":pv,"Costo_Inversion":ci,"Utilidad_Neta":pv-ci}])
                guardar(pd.concat([df_v, nv], ignore_index=True), "ventas"); st.rerun()
        st.dataframe(df_v)

    elif menu == "Gastos":
        st.header("📉 Gastos")
        df_g = leer("gastos")
        with st.form("f_g"):
            con, mon = st.text_input("Concepto"), st.number_input("Monto $")
            if st.form_submit_button("Guardar Gasto"):
                ng = pd.DataFrame([{"Fecha":datetime.now().date(),"Concepto":con,"Monto":mon}])
                guardar(pd.concat([df_g, ng], ignore_index=True), "gastos"); st.rerun()
        st.table(df_g)

    elif menu == "Informes":
        st.header("📝 Informes")
        df_inf = leer("informes")
        with st.form("f_inf"):
            c1, c2 = st.columns(2)
            cli, rif = c1.text_input("Cliente"), c1.text_input("RIF")
            ts, eq = c2.selectbox("Tipo", ["Preventivo", "Correctivo", "Instalación"]), c2.text_input("Equipo")
            fa, tr = st.text_area("Falla"), st.text_area("Trabajo")
            if st.form_submit_button("Guardar"):
                ni = pd.DataFrame([{"Fecha":datetime.now().strftime('%d/%m/%Y'),"Cliente":cli,"RIF":rif,"Tipo_Servicio":ts,"Equipo":eq,"Falla":fa,"Trabajo_Realizado":tr,"Tecnico":st.session_state.u_nom}])
                guardar(pd.concat([df_inf, ni], ignore_index=True), "informes"); st.rerun()
        st.dataframe(df_inf)

    elif menu == "Usuarios":
        st.header("👤 Gestión Staff")
        df_u = leer("usuarios_staff")
        with st.form("f_u"):
            nu, np = st.text_input("Usuario"), st.text_input("Clave")
            nr, nm = st.selectbox("Rol", ["administrador", "tecnico", "vendedor"]), st.text_input("Permisos", "Dashboard,Inventario,Informes")
            if st.form_submit_button("Crear"):
                u_n = pd.DataFrame([{"Usuario":nu,"Password":np,"Rol":nr,"Permisos":nm}])
                guardar(pd.concat([df_u, u_n], ignore_index=True), "usuarios_staff"); st.rerun()
        st.dataframe(df_u)

else:
    st.title(f"🏥 Vitrina Médica {EMPRESA}")
    inv = leer("inventario")
    if not inv.empty:
        listos = inv[inv['Estatus'] == 'Listo para Venta']
        cols = st.columns(3)
        for i, r in listos.iterrows():
            with cols[i % 3]:
                st.markdown("<div class='card-v'>", unsafe_allow_html=True)
                if r['Foto']: st.image(f"data:image/jpeg;base64,{r['Foto']}", use_container_width=True)
                st.subheader(f"{r['Marca']} {r['Modelo']}")
                st.write(f"Ref: {r['Código']} | ${r['Precio_Sugerido']:,.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
