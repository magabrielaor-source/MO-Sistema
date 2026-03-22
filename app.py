import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

# --- IDENTIDAD DE LA EMPRESA ---
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

# Función para convertir la foto a texto (Base64) para guardarla en Excel
def procesar_foto(archivo):
    if archivo is not None:
        img = Image.open(archivo)
        # Convertimos a RGB si es necesario (para evitar errores con PNG/RGBA)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Redimensionamos para que el Excel no pese demasiado
        img.thumbnail((500, 500))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        return base64.b64encode(buffer.getvalue()).decode()
    return ""

# --- ESTILOS VISUALES ---
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .card-v { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 5px solid #1e3a8a; margin-bottom: 20px; text-align: center; }
    .report-box { border: 2px solid #1e3a8a; padding: 25px; border-radius: 10px; background-color: white; color: black; }
</style>
""", unsafe_allow_html=True)

if 'rol' not in st.session_state: st.session_state.rol = 'visitante'

# --- BARRA LATERAL / LOGIN ---
with st.sidebar:
    if os.path.exists(LOGO): st.image(LOGO)
    st.title(EMPRESA)
    if st.session_state.rol == 'visitante':
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("Iniciar Sesión"):
            # Bypass de Emergencia
            if u_in == "admin" and p_in == "MO2026":
                st.session_state.update({'rol':'administrador','u_nom':'Admin Maestro','perms':["Dashboard","Inventario","Ventas","Gastos","Informes","Usuarios"]})
                st.rerun()
            
            df_u = leer("usuarios_staff")
            if not df_u.empty:
                df_u['Usuario'] = df_u['Usuario'].astype(str).str.strip()
                df_u['Password'] = df_u['Password'].astype(str).str.strip()
                m = df_u[(df_u['Usuario']==u_in.strip()) & (df_u['Password']==p_in.strip())]
                if not m.empty:
                    st.session_state.update({'rol':m.iloc[0]['Rol'],'u_nom':u_in,'perms':["Dashboard","Inventario","Ventas","Gastos","Informes","Usuarios"] if m.iloc[0]['Rol']=='administrador' else str(m.iloc[0]['Permisos']).split(',')})
                    st.rerun()
            st.error("Credenciales incorrectas")
    else:
        st.write(f"👤 **{st.session_state.u_nom}**")
        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

# --- SECCIONES ADMINISTRATIVAS ---
if st.session_state.rol != 'visitante':
    menu = st.sidebar.selectbox("Sección:", st.session_state.perms)

    if menu == "Inventario":
        st.header("📦 Gestión de Inventario Médica")
        df_inv = leer("inventario")
        
        with st.expander("➕ REGISTRAR EQUIPO NUEVO (CON FOTO)"):
            with st.form("f_inv", clear_on_submit=True):
                c1, c2 = st.columns(2)
                cod = c1.text_input("Código (SKU)")
                prd = c1.text_input("Producto")
                mar = c1.text_input("Marca")
                mod = c1.text_input("Modelo")
                ser = c2.text_input("Serial")
                ani = c2.number_input("Año del Equipo", 1990, 2030, 2012)
                
                # CAMPO DE FOTO
                foto_up = st.file_uploader("📷 Cargar Foto del Equipo", type=['jpg', 'png', 'jpeg'])
                
                c_a, c_b, c_c = st.columns(3)
                ce = c_a.number_input("Costo Ext $")
                cv = c_b.number_input("Envío $")
                cr = c_c.number_input("Reparación $")
                
                ps = st.number_input("Precio Venta Sugerido $")
                est = st.selectbox("Estatus", ["En Aduana", "En Taller", "Listo para Venta"])
                tec = st.text_input("Técnico Asignado")
                des = st.text_area("Descripción Técnica")
                
                if st.form_submit_button("Sincronizar Equipo y Foto"):
                    b64_foto = procesar_foto(foto_up)
                    nuevo_data = {
                        "Código": cod, "Producto": prd, "Marca": mar, "Modelo": mod,
                        "Serial": ser, "Año": ani, "Cantidad": 1, "Costo_Extranjero": ce,
                        "Envio_VZLA": cv, "Inversion_Reparacion": cr, "Costo_Total_Real": ce+cv+cr,
                        "Precio_Sugerido": ps, "Tecnico": tec, "Estatus": est, "Descripcion": des, "Foto": b64_foto
                    }
                    guardar(pd.concat([df_inv, pd.DataFrame([nuevo_data])], ignore_index=True), "inventario")
                    st.success("¡Equipo registrado exitosamente!"); st.rerun()

        st.subheader("Listado de Inventario")
        if not df_inv.empty:
            for i, r in df_inv.iterrows():
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    if r['Foto']:
                        col1.image(f"data:image/jpeg;base64,{r['Foto']}", use_container_width=True)
                    else:
                        col1.info("Sin Foto")
                    col2.write(f"### {r['Marca']} {r['Modelo']} (REF: {r['Código']})")
                    col2.write(f"**Estatus:** {r['Estatus']} | **Año:** {r['Año']} | **Serial:** {r['Serial']}")
                    st.divider()

    elif menu == "Dashboard":
        st.header("📊 Dashboard Financiero")
        inv = leer("inventario")
        if not inv.empty:
            inv['Costo_Total_Real'] = pd.to_numeric(inv['Costo_Total_Real'], errors='coerce').fillna(0)
            st.metric("Inversión Total en Equipos", f"${inv['Costo_Total_Real'].sum():,.2f}")
            st.write(f"Equipos registrados: {len(inv)}")

    elif menu == "Usuarios":
        st.header("👤 Gestión de Staff")
        df_u = leer("usuarios_staff")
        with st.form("f_u"):
            nu, np = st.text_input("Nuevo Usuario"), st.text_input("Nueva Clave")
            nr = st.selectbox("Rol", ["administrador", "tecnico", "vendedor"])
            nm = st.text_input("Permisos (Dashboard,Inventario...)", "Dashboard,Inventario,Informes")
            if st.form_submit_button("Crear Staff"):
                u_n = pd.DataFrame([{"Usuario":nu, "Password":np, "Rol":nr, "Permisos":nm}])
                guardar(pd.concat([df_u, u_n], ignore_index=True), "usuarios_staff")
                st.success("Usuario Creado"); st.rerun()
        st.dataframe(df_u)

    elif menu == "Informes":
        st.header("📝 Orden de Servicio Técnico")
        df_inf = leer("informes")
        with st.form("f_inf"):
            c1, c2 = st.columns(2)
            cli, rif = c1.text_input("Cliente"), c1.text_input("RIF")
            ts, eq = c2.selectbox("Tipo de Servicio", ["Preventivo", "Correctivo", "Instalación"]), c2.text_input("Equipo")
            fa, tr = st.text_area("Falla Reportada"), st.text_area("Trabajo Realizado")
            if st.form_submit_button("Guardar Reporte"):
                n_i = pd.DataFrame([{"Fecha":datetime.now().strftime('%d/%m/%Y'), "Cliente":cli, "RIF":rif, "Tipo_Servicio":ts, "Equipo":eq, "Falla":fa, "Trabajo_Realizado":tr, "Tecnico":st.session_state.u_nom}])
                guardar(pd.concat([df_inf, n_i], ignore_index=True), "informes")
                st.success("Reporte Guardado"); st.rerun()
        st.dataframe(df_inf)

else:
    # --- VITRINA PÚBLICA ---
    st.markdown(f"<h1 style='text-align:center; color:#1e3a8a;'>VITRINA MÉDICA {EMPRESA}</h1>", unsafe_allow_html=True)
    inv = leer("inventario")
    if not inv.empty:
        listos = inv[inv['Estatus'] == 'Listo para Venta']
        cols = st.columns(3)
        for i, r in listos.iterrows():
            with cols[i % 3]:
                st.markdown("<div class='card-v'>", unsafe_allow_html=True)
                if r['Foto']:
                    st.image(f"data:image/jpeg;base64,{r['Foto']}", use_container_width=True)
                st.subheader(f"{r['Marca']} {r['Modelo']}")
                st.write(f"Ref: {r['Código']}")
                st.write(f"**Precio: ${r['Precio_Sugerido']:,.2f}**")
                st.markdown("</div>", unsafe_allow_html=True)
