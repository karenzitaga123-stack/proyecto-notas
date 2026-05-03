import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from io import BytesIO
from reportlab.pdfgen import canvas
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO PROFESIONAL ---
st.set_page_config(page_title="EduConnect LMS Pro", layout="wide", page_icon="🎓")

# Estilo Institucional: Blanco, Gris, Azul y Rojo
st.markdown("""
    <style>
    :root { --azul: #003366; --rojo: #C8102E; --gris: #F4F4F4; }
    .main { background-color: var(--gris); }
    .stButton>button { 
        background-color: var(--azul); color: white; border-radius: 10px; 
        font-weight: bold; border: none; height: 3em; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { background-color: var(--rojo); transform: scale(1.02); }
    .card { 
        background: white; padding: 25px; border-radius: 15px; 
        border-top: 5px solid var(--rojo); box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: var(--azul); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE BASE DE DATOS ---
def get_connection():
    return sqlite3.connect('educonnect_final.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, pw TEXT, nombre TEXT, rol TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notas 
                 (alumno_email TEXT, materia TEXT, nota REAL, periodo TEXT, 
                 PRIMARY KEY(alumno_email, materia, periodo))''')
    conn.commit()
    conn.close()

init_db()

# --- 3. FUNCIONES DE LÓGICA DE NEGOCIO ---
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def export_pdf(nombre, df):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, f"REPORTE ACADÉMICO OFICIAL: {nombre}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Fecha de emisión: {datetime.now().strftime('%Y-%m-%d')}")
    p.line(100, 770, 500, 770)
    y = 740
    for _, row in df.iterrows():
        p.drawString(100, y, f"{row['materia']} - {row['periodo']}: {row['nota']}")
        y -= 20
    p.save()
    return buffer.getvalue()

# --- 4. SISTEMA DE LOGIN Y REGISTRO MEJORADO ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col_img, col_form = st.columns([1.4, 1])
    
    with col_img:
        st.image("assets/bienvenida.jfif", 
                 caption="Excelencia, Liderazgo y Valores")
        st.title("Sistema de Gestión Educativa")
        st.info("Portal abierto: Regístrese como Profesor para calificar o como Estudiante para ver su progreso.")

    with col_form:
        menu_acc = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with menu_acc[0]: # LOGIN
            email_log = st.text_input("Correo Institucional", placeholder="ejemplo@correo.com")
            pw_log = st.text_input("Contraseña", type="password")
            if st.button("Acceder al Sistema"):
                conn = get_connection()
                user = conn.execute("SELECT * FROM usuarios WHERE email=? AND pw=?", 
                                    (email_log, hash_pw(pw_log))).fetchone()
                conn.close()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user 
                    st.rerun()
                else:
                    st.error("Credenciales no válidas. Si es nuevo, regístrese en la otra pestaña.")

        with menu_acc[1]: # REGISTRO
            new_name = st.text_input("Nombre Completo")
            new_email = st.text_input("Correo Electrónico")
            new_pw = st.text_input("Cree su Contraseña", type="password")
            new_rol = st.selectbox("Tipo de Usuario", ["Estudiante", "Profesor"])
            if st.button("Finalizar Registro"):
                if new_name and new_email and new_pw:
                    try:
                        conn = get_connection()
                        conn.execute("INSERT INTO usuarios (email, pw, nombre, rol) VALUES (?,?,?,?)", 
                                    (new_email, hash_pw(new_pw), new_name, new_rol))
                        conn.commit()
                        # Auto-login automático tras registrarse
                        user = conn.execute("SELECT * FROM usuarios WHERE email=?", (new_email,)).fetchone()
                        conn.close()
                        st.session_state.logged_in = True
                        st.session_state.user_info = user
                        st.success("¡Cuenta creada exitosamente!")
                        st.rerun()
                    except:
                        st.error("Este correo ya está registrado.")
                else:
                    st.warning("Complete todos los campos.")

# --- 5. PANEL DE CONTROL COMPLETO (LMS) ---
else:
    u_id, u_email, u_pw, u_nombre, u_rol = st.session_state.user_info
    
    st.sidebar.image("assets/incio.jfif", width=150)
    st.sidebar.title(f"Bienvenido, \n{u_nombre}")
    st.sidebar.write(f"Rol: *{u_rol}*")
    
    if u_rol == "Profesor":
        opcion = st.sidebar.radio("Menú Docente", ["Gestión de Calificaciones", "Noticias Escolares", "Salir"])
        
        if opcion == "Gestión de Calificaciones":
            st.header("🍎 Carpeta del Profesor: Calificar")
            conn = get_connection()
            alumnos = pd.read_sql("SELECT email, nombre FROM usuarios WHERE rol='Estudiante'", conn)
            conn.close()
            
            if not alumnos.empty:
                sel_alumno = st.selectbox("Seleccione un Alumno", alumnos['nombre'])
                mail_alumno = alumnos[alumnos['nombre'] == sel_alumno]['email'].values[0]
                
                c1, c2, c3 = st.columns(3)
                mat = c1.selectbox("Asignatura", ["Matemáticas", "Física", "Química", "Literatura", "Historia"])
                not_val = c2.number_input("Nota (0.0 - 5.0)", 0.0, 5.0, 4.0)
                per = c3.selectbox("Periodo Académico", ["Corte 1", "Corte 2", "Examen Final"])
                
                if st.button("📤 Guardar/Actualizar Nota"):
                    conn = get_connection()
                    conn.execute("INSERT OR REPLACE INTO notas VALUES (?,?,?,?)", (mail_alumno, mat, not_val, per))
                    conn.commit()
                    conn.close()
                    st.toast(f"Nota registrada para {sel_alumno}", icon="✅")
            else:
                st.warning("Aún no hay estudiantes registrados en la base de datos.")

    else: # ROL ESTUDIANTE
        opcion = st.sidebar.radio("Menú Estudiantil", ["Mi Portal", "Material de Estudio", "Eventos", "Salir"])
        
        if opcion == "Mi Portal":
            st.header("📊 Mis Calificaciones y Boletín")
            conn = get_connection()
            mis_notas = pd.read_sql(f"SELECT materia, nota, periodo FROM notas WHERE alumno_email='{u_email}'", conn)
            conn.close()
            
            if not mis_notas.empty:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.table(mis_notas)
                st.markdown('</div>', unsafe_allow_html=True)
                
                pdf_file = export_pdf(u_nombre, mis_notas)
                st.download_button("📥 Descargar Boletín Digital (PDF)", data=pdf_file, file_name=f"Boletin_{u_nombre}.pdf")
            else:
                st.info("Aún no tienes calificaciones registradas por tus profesores.")
                st.image("https://unsplash.com", caption="Biblioteca Digital")

        elif opcion == "Material de Estudio":
            st.header("📚 Recursos de Aprendizaje")
            st.markdown("""
            - [📖 Guía de Matemáticas Avanzadas](https://google.com)
            - [🎥 Laboratorio Virtual de Química](https://colorado.edu)
            - [📝 Repositorio de Lecturas - Literatura](https://gutenberg.org)
            """)
            st.image("assets/otro.jfif")

        elif opcion == "Eventos":
            st.header("📅 Calendario y Actividades")
            st.markdown('<div class="card"><h4>Próximos Eventos:</h4>'
                        '<ul><li>Feria de Ciencias: 15 de Octubre</li>'
                        '<li>Exámenes de Periodo: 20-25 de Octubre</li>'
                        '<li>Día del Deporte: 5 de Noviembre</li></ul></div>', unsafe_allow_html=True)

    if opcion == "Salir":
        st.session_state.logged_in = False
        st.rerun()