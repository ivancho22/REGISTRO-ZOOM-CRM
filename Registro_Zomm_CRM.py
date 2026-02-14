import streamlit as st
from sqlalchemy import text
import time
import os
from sqlalchemy import create_engine
from sqlalchemy import create_engine, text
import pandas as pd

# 1. Cargar credenciales desde los Secrets de Streamlit
creds = st.secrets["db_credentials"]
DB_USER = creds["user"]
DB_PASS = creds["pass"]
DB_HOST = creds["host"]
DB_NAME = creds["name"]

# 2. Crear el motor de conexión
# Agregamos pool_pre_ping para que la conexión no se caiga durante el evento
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}",
    pool_pre_ping=True
)

# --- 3. LÓGICA DINÁMICA: LEER CURSO DESDE URL ---
# Detecta el parámetro ?curso= en la URL
params = st.query_params
slug_curso = params.get("curso")

if not slug_curso:
    st.warning("⚠️ Por favor, accede a través del enlace oficial enviado por MB Educación.")
    st.stop()

# Buscar datos del curso en la tabla agenda_cursos
with engine.connect() as conn:
    query_busqueda = text("SELECT titulo_curso, link_zoom FROM agenda_cursos WHERE slug = :s AND estado = 'activo'")
    resultado = conn.execute(query_busqueda, {"s": slug_curso}).fetchone()

if resultado:
    titulo_evento = resultado[0]
    link_zoom_final = resultado[1]
else:
    st.error("🚫 Lo sentimos, este curso no existe, ya finalizó o el enlace es incorrecto.")
    st.stop()

# --- 4. INTERFAZ VISUAL DINÁMICA ---
# from tu_archivo_principal import engine 

st.title("Registro de Asistencia y Tratamiento de Datos")
st.subheader(f"Bienvenido al {titulo_evento}") # Título automático

with st.form("registro_publico", clear_on_submit=True):
    nombre = st.text_input("Nombre Completo *")
    institucion = st.text_input("Institución Educativa /Empresa /Asociacion *")
    rol_cargo = st.text_input(" Cargo en la Institución Educativa /Empresa /Asociacion*")
    email = st.text_input("Correo Electrónico")
    
    st.markdown("---")
    st.write("🔒 **Política de Tratamiento de Datos**")
    st.caption("Al marcar la casilla, autoriza a MB Educación a utilizar sus datos para fines informativos y académicos según la Ley 1581 de 2012.")
    acepta = st.checkbox("Acepto el tratamiento de mis datos personales")
    
    boton_registro = st.form_submit_button("REGISTRARME E INGRESAR A ZOOM")

if boton_registro:
    if nombre and institucion and acepta: # Añadí 'acepta' a la validación
        try:
            with engine.begin() as conn:
                # Buscamos también el slug en el query inicial para tenerlo a mano
                query = text("""
                    INSERT INTO directorio_tratamiento 
                    (contacto_nombre, institucion, rol_cargo, email, habeas_data, canal_autorizacion) 
                    VALUES (:nom, :inst, :rol, :mail, :hab, :cnal)
                """)
                
                # CAMBIO CLAVE: Incluimos el slug_curso en el canal para que el CRM lo rastree
                # Formato: "Streaming: [Slug] - [Fecha]"
                fecha_hoy = time.strftime('%d/%m/%Y')
                canal_info = f"Streaming: {slug_curso} | {titulo_evento} - {fecha_hoy}"
                
                conn.execute(query, {
                    "nom": nombre, 
                    "inst": institucion, 
                    "mail": email,
                    "rol": rol_cargo,
                    "hab": 1,
                    "cnal": canal_info
                })
            
            st.success(f"¡Registro exitoso para {titulo_evento}!")
            st.balloons()
            
            st.info("🔄 Redirigiendo a la sala de Zoom en 3 segundos...")
            time.sleep(3) # Pausa pequeña para que vean el mensaje
            
            # Botón de respaldo por si el navegador bloquea ventanas emergentes
            st.link_button("👉 CLICK AQUÍ PARA ENTRAR AHORA", link_zoom_final)
            
            # Redirección automática
            js = f'<script>window.location.href = "{link_zoom_final}";</script>'
            st.components.v1.html(js, height=0)
            
        except Exception as e:
            st.error(f"Error detallado: {str(e)}")
    elif not acepta:
        st.warning("Debe aceptar el tratamiento de datos para ingresar.")
    else:
        st.warning("Por favor completa los campos obligatorios (*)")




