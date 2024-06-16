import tkinter as tk
from tkinter import ttk, Canvas
from PIL import Image, ImageTk
import dlib
import cv2
import os
import util
from register_user import RegisterUserApp
from test import test
import time
import socket
import threading
import queue
import subprocess
import pygame
import uuid 
from pymongo import MongoClient
from datetime import datetime, timedelta
from mongo_connection import add_open_schedule_check, get_db, get_employee_schedule_type, get_info, get_admin_message_by_rfc, verificar_y_actualizar_horario_fechas
import pytz

line_y = 0
direction = 1  
external_process = None



def create_gradient(canvas, start_color, end_color, width):
    """ Create a horizontal gradient with the given start and end RGB colors """
    (r1, g1, b1) = canvas.winfo_rgb(start_color)
    (r2, g2, b2) = canvas.winfo_rgb(end_color)
    
    r_ratio = float(r2 - r1) / width
    g_ratio = float(g2 - g1) / width
    b_ratio = float(b2 - b1) / width

    for i in range(width):
        nr = int(r1 + (r_ratio * i))
        ng = int(g1 + (g_ratio * i))
        nb = int(b1 + (b_ratio * i))
        color = "#%4.4x%4.4x%4.4x" % (nr, ng, nb)
        canvas.create_line(i, 0, i, 10, tags=("gradient",), fill=color)

    canvas.lower("gradient")  


def load_resized_image(path, size):
   
    image = Image.open(path)
    image = image.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(image)

def update_time(time_label, root):
    current_time = datetime.now().strftime('%I:%M:%S %p')
    time_label.config(text=current_time)
    root.after(1000, update_time, time_label, root)
    
dias_espanol = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
    }

def update_date(date_label):
    day_of_week = datetime.now().strftime("%A")
    date_str = datetime.now().strftime("%d/%m/%Y").upper()
    day_of_week_es = dias_espanol[day_of_week]
    current_date = f"{day_of_week_es}\n\n{date_str}"
    date_label.config(text=current_date)


    
def play_success_sound():
        success_sound = pygame.mixer.Sound('imagenes_ui/correcto.wav')  
        success_sound.play()

   
def play_error_sound():
        error_sound = pygame.mixer.Sound('imagenes_ui/Error.wav')  
        error_sound.play()
        
def play_notification_sound():
    notification_sound = pygame.mixer.Sound('imagenes_ui/correcto.wav')
    notification_sound.play()
    return notification_sound


# sonidos para los estatus de entrada y salida
def  play_normal_sound():
    normal_sound = pygame.mixer.Sound('imagenes_ui/normal.wav')
    normal_sound.play()
    
def play_falta_sound(): 
    falta_sound = pygame.mixer.Sound('imagenes_ui/falta.wav')
    falta_sound.play()
    
def play_nota_mala_sound():
    nota_mala_sound = pygame.mixer.Sound('imagenes_ui/nota_mala.wav')
    nota_mala_sound.play()

def play_retardo_sound():
    retardo_sound = pygame.mixer.Sound('imagenes_ui/retardo.wav')
    retardo_sound.play()

def play_error_escaneo():
    error_escaneo = pygame.mixer.Sound('imagenes_ui/error_escanear.wav')
    error_escaneo.play()

def play_ya_scaneado():
    ya_scaneado= pygame.mixer.Sound('imagenes_ui/Ya_escaneado.wav')
    ya_scaneado.play()

### SALIDAS ###
def play_sa_normal():
    salida_normal= pygame.mixer.Sound('imagenes_ui/SALIDA_NORMAL-.wav')
    salida_normal.play()

def play_sa_retardo():
    salida_retado= pygame.mixer.Sound('imagenes_ui/SALIDA_CON_RETARDO.wav')
    salida_retado.play()

def play_sa_notamala():
    salida_notamala= pygame.mixer.Sound('imagenes_ui/SALIDA_CON_NOTA_MALA.wav')
    salida_notamala.play()

def play_sa_falta():
    salida_falta= pygame.mixer.Sound('imagenes_ui/SALIDA_CON_FALTA.wav')
    salida_falta.play()




class App:
    def __init__(self, root, parent_frame, section2_frame, section4_frame):
        self.root = root
        self.detector = dlib.get_frontal_face_detector()
        self.tracker = dlib.correlation_tracker()
        self.tracking_face = False
        
        self.main_frame = parent_frame
        self.webcam_label = tk.Label(self.main_frame)
        self.webcam_label.grid(row=0, column=0, sticky='nswe')
        self.add_webcam(self.webcam_label)
        self.section2_frame = section2_frame
        self.section4_frame = section4_frame
        self.db = get_db()
        self.update_section2()
        self.message_queue = queue.Queue()
        self.start_socket_server()
        
        self.metodo_verificacion = None
        
  
        resized_image1 = load_resized_image('RECURSOS/H.png', (90, 100))
        self.image_label1 = tk.Label(self.section4_frame, image=resized_image1, bg='#D3D3D3')
        self.image_label1.grid(row=0, column=0, sticky='nswe')
        self.image_label1.image = resized_image1  

        resized_image2 = load_resized_image('RECURSOS/R.png', (90, 90))
        self.image_label2 = tk.Label(self.section4_frame, image=resized_image2, bg='#D3D3D3')
        self.image_label2.grid(row=0, column=2, sticky='nswe')
        self.image_label2.image = resized_image2  
        
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.log_path = './log.txt'
        self.most_recent_capture_arr = None
        self.error_count = 0 

   # ------------------------------------ PARA AVISOS TRABAJADOR 2 MODULOS ------------------------------------ #
    def procesar_rfc(self, rfc):
        # Aquí va la lógica para procesar el RFC
        print(f"Procesando RFC: {rfc}")
        # Supongamos que necesitas buscar información relacionada con este RFC en la base de datos
        info_rfc = self.db.get_collection('Avisos').find_one({'RFC': rfc})
        if info_rfc:
            print("Información encontrada:", info_rfc)
        else:
            print("No se encontró información para el RFC proporcionado.")

    def register_facial_entry(self, name, entry_type, success):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = "exitoso" if success else "fallido"
        entry_id = str(uuid.uuid4())
        log_entry = f"{timestamp} - ID: {entry_id}, Método: Reconocimiento Facial, Nombre: {name}, Tipo: {entry_type}, Resultado: {result}\n"

        with open(self.log_path, 'a') as f:
            f.write(log_entry)
        
         # Comprobar si el nombre (que es el RFC) tiene un mensaje de administrador asociado
        admin_message = get_admin_message_by_rfc(self.db, name)
        if admin_message and admin_message != "No se encontró el RFC en la base de datos." and not admin_message.startswith("Error"):
            
            notification_sound = play_notification_sound()
            pygame.time.wait(int(notification_sound.get_length() * 1000))
            
            self.show_admin_message(admin_message)

    
    def show_admin_message(self, message):
        """
        Muestra un mensaje de administrador en una ventana emergente que se ajusta al tamaño del mensaje
        y se cierra automáticamente después de 5 segundos.
        """
        top = tk.Toplevel(self.main_frame)
    
  

        top_x = (top.winfo_screenwidth() - 500) // 2
        top_y = (top.winfo_screenheight() - 300) // 2
        top.geometry(f"+{top_x}+{top_y}")
        
        top.grab_set()  # Evita que se interactúe con la ventana principal mientras esta esté abierta

        # No se especifica geometry() para que se ajuste al contenido automáticamente
        top.focus_force()  # Pone el foco en la ventana emergente

        # Crear un label con el mensaje y empaquetarlo con un poco de padding
        msg_label = tk.Label(top, text=message, font=('Arial', 20), wraplength=350,bd=0)  # Ajusta wraplength según lo necesario
        msg_label.pack(pady=20, padx=20, expand=True)

        # Ajusta la ventana para que se centre sobre la ventana principal
        top.transient(self.main_frame)  # Hace que la ventana flotante esté vinculada a la ventana principal
      
        # Programa el cierre automático de la ventana después de 5000 milisegundos (5 segundos)
        top.after(5000, top.destroy)
    
      # ------------------------------------ TERMINA AVISOS TRABAJADOR ------------------------------------ #


    # ------------------------------------ PARA AVISOS GENERALES 1 MODULO -------------------------------- #



    def register_fingerprint_entry(self, name, entry_type, success):
        # Método para registrar la entrada por reconocimiento de huella dactilar
        with open(self.log_path, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result = "exitoso" if success else "fallido"
            entry_id = str(uuid.uuid4())

            log_entry = f"{timestamp} - ID: {entry_id}, Método: Huella Dactilar, Nombre: {name}, Tipo: {entry_type}, Resultado: {result}\n"
            f.write(log_entry)
            
            with open(self.log_path, 'a') as f:
                f.write(log_entry)
        
         # Comprobar si el nombre (que es el RFC) tiene un mensaje de administrador asociado
        admin_message = get_admin_message_by_rfc(self.db, name)
        if admin_message and admin_message != "No se encontró el RFC en la base de datos." and not admin_message.startswith("Error"):
            notification_sound = play_notification_sound()
            pygame.time.wait(int(notification_sound.get_length() * 1000))
            
            self.show_admin_message(admin_message)
            

    def update_section2(self):
            try:
                # Intenta obtener la información del campo específico
                info = get_info(self.db, 'Avisogeneral')
                if info is None:
                    info = "No hay mensaje disponible."

                for widget in self.section2_frame.winfo_children():
                    widget.destroy()
                    
            except KeyError:
                # En caso de que el campo 'mensaje_administrador' no exista
                info = "El campo requerido no está disponible en la base de datos."
            except Exception as e:
                # Para cualquier otro error que pueda surgir
                info = f"Error al obtener la información: {str(e)}"

            # Limpia el frame y actualiza con la nueva información
            for widget in self.section2_frame.winfo_children():
                widget.destroy()
            info_label = tk.Label(self.section2_frame, text=info, bg='#EFEFEF', fg='black', anchor='center', font=('Roboto', 20))
            info_label.pack(expand=True, fill='both')

    """def daily_update(self):
        self.update_section2()
        # Calcula el tiempo hasta la medianoche del día siguiente
        now = datetime.now()
        midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        seconds_until_midnight = (midnight - now).seconds
        # Configura un temporizador para actualizar al siguiente día
        threading.Timer(seconds_until_midnight, self.daily_update).start()"""

            
    def start_socket_server(self):
     
        threading.Thread(target=self.init_socket_server, daemon=True).start()
    def init_socket_server(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.bind(("localhost", 12345))
            servidor.listen()
            while True:
                conexion, direccion = servidor.accept()
                threading.Thread(target=self.handle_client, args=(conexion, direccion), daemon=True).start()
                
    def handle_client(self, conexion, direccion):
        toque_contador = 0  
        external_process = None 
        try:
            while True:
                datos = conexion.recv(1024)
                if not datos:
                    break 
                mensaje_completo = datos.decode("ascii").strip()
              
                if mensaje_completo == "CERRAR_CONEXION":
                    print(f"Cerrando conexión con {direccion}")
                    break
              
                if mensaje_completo == "El lector fue tocado":
                    toque_contador += 1
                 
                    if toque_contador >= 2:
                        self.message_queue.put("No ha podido tomar su asistencia")
                        toque_contador = 0  
                        
                        if external_process is not None:
                            external_process.terminate()
                        external_process.wait() 
                    
                    #external_process = subprocess.Popen(["C:/Users/isc20/source/repos/codigos-para-lector-de-huella/DemoDP4500/bin/Debug/DemoDP4500.exe", "verificar"])

                else:
                    
                    self.message_queue.put(mensaje_completo)
                    toque_contador = 0
        except Exception as e:
            print(f"Error al manejar al cliente {direccion}: {e}")
        finally:
            conexion.close()  
  
    
    # funcion donde se recibe el id de las huellas y se seperan para solo tomar el rfc (ID)
    """""
    
     *se recibe el id de la huella y se separa para solo tomar el rfc (ID)
     *se accede a la base de datos dediante las funciones del script mongo conecction
     *se accede a los hoarios (documentos) de acuerod al rfc recibido
     
     
    """
    def check_for_messages(self):
        self.metodo_verificacion = 'huella'
        while not self.message_queue.empty():
            mensaje_completo = self.message_queue.get_nowait()
            print(f"Mensaje recibido: {mensaje_completo}")

            if mensaje_completo == "FalloCapturaHuella":
                self.msg_box_huella('Error de Lector', 'No se ha podido capturar la huella. Verifica el lector y vuelve a intentarlo.', 'error')
                self.mostrar_error()
                self.register_fingerprint_entry(None, 'Fallo lector', False)
                continue

            partes = mensaje_completo.split(": ")
            accion = partes[0]
            idHuella = partes[1] if len(partes) > 1 else ""

            if accion == "Asistencia tomada":
                schedule_type = get_employee_schedule_type(self.db, idHuella)
                if schedule_type == 'Abierto':
                    mensaje = add_open_schedule_check(self.db, idHuella, "entrada")
                    self.msg_box_huella('Registro de Asistencia', mensaje, 'éxito')
                    self.register_fingerprint_entry(idHuella, 'Entrada Exitosa', True)
                    if message == f"Entrada registrada con éxito {idHuella}. ¡Bienvenido de nuevo!":
                        play_normal_sound()
                    elif message == f"Bienvenido {idHuella}, llegaste a tiempo. Asistencia tomada.":
                        play_normal_sound()
                    elif message == f"Hasta luego {idHuella}, salida registrada a tiempo.":
                        play_sa_normal()
                elif schedule_type == 'Cerrado':
                    result = verificar_y_actualizar_horario_fechas(self.db, idHuella)
                    if isinstance(result, tuple):
                        estatus, action_type = result
                    else:
                            self.msg_box('Error', result, 'error')
                    if estatus:
                        status_messages = {
                            "NORMAL": {
                                "entrada": f"Bienvenido {idHuella}, llegaste a tiempo, asistencia tomada.",
                                "salida": f"Hasta luego {idHuella}, salida registrada a tiempo."
                            },
                            "RETARDO": {
                                "entrada": f"¡CASI! {idHuella}, llegaste un poco tarde, asistencia tomada con retardo.",
                                "salida": f"¡CUIDADO! {idHuella}, has salido tarde."
                            },
                            "NOTA MALA": {
                                "entrada": f"¡UPSS! {idHuella}, esta vez tienes nota mala, llegaste tarde.",
                                "salida": f"¡ALERTA! {idHuella}, has salido mucho más tarde de lo previsto."
                            }
                        }
                        message_types = {
                            "NORMAL": "éxito",
                            "RETARDO": "retardo",
                            "NOTA MALA": "fueraderango"
                        }
                        message = status_messages.get(estatus, {}).get(action_type, "Ya escaneado o  fuera de rango.")
                        #ction_config = status_messages.get(estatus, {}).get(action_type, None)
                        print(message)

                        if message == "Ya escaneado o  fuera de rango.":
                            play_ya_scaneado()
                        
                        elif message == f"Bienvenido {idHuella}, llegaste a tiempo, asistencia tomada.":
                            play_normal_sound()
                        
                        elif message == f"Hasta luego {idHuella}, salida registrada a tiempo.":
                            play_sa_normal()
                        
                        elif message == f"¡CASI! {idHuella}, llegaste un poco tarde, asistencia tomada con retardo.":
                            play_retardo_sound()

                        elif message == f"¡CUIDADO! {idHuella}, has salido tarde.":
                            play_sa_retardo()

                        elif message == f"¡UPSS! {idHuella}, esta vez tienes nota mala, llegaste tarde.":
                            play_nota_mala_sound()

                        elif message == f"¡ALERTA! {idHuella}, has salido mucho más tarde de lo previsto.":
                            play_sa_notamala()

                        elif message == "Ya escaneado o  fuera de rango.":
                            play_ya_scaneado()

                        mensaje = f"{estatus} - {action_type}"  # Ajustar mensaje según necesidad
                        message_type = message_types.get(estatus, "error")  # Default to "error" if status is unrecognized
                        self.msg_box('Registro de Asistencia', message, message_type)
                        self.register_fingerprint_entry(idHuella, 'Entrada Exitosa' if estatus == "NORMAL" else 'Entrada Fallida', estatus == "NORMAL")
                    else:
                        self.msg_box_huella('Error de Asistencia', result, 'error')

            elif accion == "Escaneo fallido":
                play_error_sound()
                self.mostrar_error()
                self.register_fingerprint_entry(idHuella, 'Entrada Fallida', False)

            elif mensaje_completo == "Usuario no registrado, o intentelo de nuevo":
                #lay_error_sound()
                self.mostrar_usuario_no_registrado()
                self.register_fingerprint_entry(idHuella, 'Usuario no registrado', False)
            else:
                print("Acción no reconocida.")

        self.main_frame.after(100, self.check_for_messages)


    def msg_box_huella(self, title, message, message_type):
        colors = {
            'error': '#FF0000',       # Rojo
            'éxito': '#008000',       # Verde
            'retardo': '#FFFF00',     # Amarillo
            'fueraderango': '#8A2BE2' # Morado
        }
        background_color = colors.get(message_type, '#D3D3D3')

        # Reproducir sonido según el tipo de mensaje
        if message_type == 'éxito':
            play_normal_sound()
        #elif message_type == 'retardo':
          #  play_retardo_sound()
        #elif message_type == 'fueraderango':
          #  play_falta_sound()
        elif message_type == 'error':
            play_error_sound()

        # Limpiar los widgets existentes en section2_frame
        for widget in self.section2_frame.winfo_children():
            widget.destroy()

        # Configurar el contenedor de mensajes
        msg_container = tk.Frame(self.section2_frame, bg='white', borderwidth=2, relief="groove")
        msg_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Formatear y mostrar el mensaje
        current_time = datetime.now().strftime("%H:%M:%S")
        current_day = dias_espanol[datetime.now().strftime("%A")]
        current_date = datetime.now().strftime("%d / %m / %Y")
        full_message = f"{title}\n{message}\n\nHora: {current_time}\nDía: {current_day}\nFecha: {current_date}"

        message_label = tk.Label(msg_container, text=full_message, bg='white', font=('Arial', 18), wraplength=480, justify=tk.CENTER)
        message_label.pack(expand=True, fill='both', padx=20, pady=20)

        # Cambiar el color de fondo de image_label1 y restablecerlo después de un tiempo
        self.image_label1.config(bg=background_color)
        self.image_label1.after(9000, lambda: self.image_label1.config(bg='#D3D3D3'))

        # Restablecer el fondo del section2_frame después de 9 segundos
        self.section2_frame.after(9000, self.update_section2)
        
        
    def mostrar_usuario_no_registrado(self):
        self.metodo_verificacion = 'huella'

        for widget in self.section2_frame.winfo_children():
            widget.destroy()

        current_time = datetime.now().strftime("%H:%M:%S")  # Corregido aquí
        current_day = dias_espanol[datetime.now().strftime("%A")]  # Corregido aquí
        current_date = datetime.now().strftime("%d / %m / %Y")  # Corregido aquí


      
        error_bg_color = '#FFCCCC'  # Un color de fondo rojo claro para indicar un error
        error_message = f"Usuario no registrado. Por favor, regístrese o intente nuevamente.\n\nHora: {current_time}\nDía: {current_day}\nFecha: {current_date}"

  
        error_container = tk.Frame(self.section2_frame, borderwidth=2, relief="groove")
        error_container.pack(expand=False, fill='both', padx=10, pady=10)
        error_container.pack_propagate(False) 
        error_container.place(relx=0.5, rely=0.5, anchor='center', width=800, height=380)

  
        error_label = tk.Label(error_container, text=error_message,  fg='black', font=('Arial', 18), wraplength=480, justify=tk.CENTER)
        error_label.pack(expand=True, fill='both', padx=20, pady=20)

        self.section2_frame.after(8000, self.update_section2)
        self.image_label1.config(bg='#FF0000')
        self.image_label1.after(8000, lambda: self.image_label1.config(bg='#D3D3D3'))

        
  
    def mostrar_error(self):
        for widget in self.section2_frame.winfo_children():
            widget.destroy()

        current_time = datetime.now().strftime("%H:%M:%S")  # Corregido aquí
        current_day = dias_espanol[datetime.now().strftime("%A")]  # Corregido aquí
        current_date = datetime.now().strftime("%d / %m / %Y")  # Corregido aquí

        error_message = f"El escaneo ha fallado. Por favor, intenta nuevamente.\n\nHora: {current_time}\nDía: {current_day}\nFecha: {current_date}"
        error_container = tk.Frame(self.section2_frame, borderwidth=2, relief="groove")
        error_container.pack(expand=False, fill='both', padx=10, pady=10)
        error_container.pack_propagate(False)
        error_container.place(relx=0.5, rely=0.5, anchor='center', width=800, height=380)

        error_label = tk.Label(error_container, text=error_message, fg='black', font=('Arial', 18), wraplength=480, justify=tk.CENTER)
        error_label.pack(expand=True, fill='both', padx=20, pady=20)

        self.section2_frame.after(8000, self.update_section2)


    def msg_box(self, title, message, message_type):
        for widget in self.section2_frame.winfo_children():
            widget.destroy()

        color_map = { 
            'escaneando': '#D3D3D3',  # Gris
            'error': '#FF0000',  # Rojo
            'éxito': '#008000',  # Verde
            'retardo': '#E3DB1B',
            'fueraderango': '#941EDD'
        }
        
        background_color = color_map.get(message_type, '#D3D3D3') 
        
    
        if message_type == 'error':
            #play_error_sound()
            if self.metodo_verificacion == 'facial':
                label_a_cambiar = self.image_label2
            elif self.metodo_verificacion == 'huella':
                label_a_cambiar = self.image_label1
            label_a_cambiar.config(bg=color_map['error'])
    
            label_a_cambiar.after(9000, lambda: label_a_cambiar.config(bg='#D3D3D3'))
        else:
            if self.metodo_verificacion == 'facial':
                #play_success_sound()
                label_a_cambiar = self.image_label2
            elif self.metodo_verificacion == 'huella':
                label_a_cambiar = self.image_label1
            label_a_cambiar.config(bg=background_color)
            label_a_cambiar.after(9000, lambda: label_a_cambiar.config(bg='#D3D3D3'))


        label_a_cambiar.config(bg=background_color)
   
        message_container = tk.Frame(self.section2_frame, bg='white', borderwidth=2, relief="groove")
        message_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        current_time = datetime.now().strftime("%H:%M:%S")
        current_day = dias_espanol[datetime.now().strftime("%A")]
        current_date = datetime.now().strftime("%d / %m / %Y")
        full_message = f"{title}\n{message}\n\nHora: {current_time}\nDía: {current_day}\nFecha: {current_date}"
        
        # error_label = tk.Label(error_container, text=error_message, bg=error_bg_color, fg='black', font=('Arial', 18), wraplength=480, justify=tk.CENTER)
        # error_label.pack(expand=True, fill='both', padx=20, pady=20)
        
        message_label = tk.Label(message_container, text=full_message, bg='white', font=('Arial', 18),wraplength=480,justify=tk.CENTER)
        message_label.pack(expand=True, fill='both', padx=20, pady=20)


        self.image_label2.after(9000, lambda: self.image_label2.config(bg='#D3D3D3')) 
        self.image_label1.after(9000, lambda: self.image_label1.config(bg='#D3D3D3'))
        self.section2_frame.after(9000, self.update_section2)

    
    def add_webcam(self, label):
        self.cap = cv2.VideoCapture(0)
 
        
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
        

        #self.cap.set(cv2.CAP_PROP_FPS, 30)
        self._label = label
        self.process_webcam()


    def process_webcam(self):
    
        try:
            self.metodo_verificacion = 'facial'

            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                return
            frame = cv2.flip(frame, 1)  # Refleja el frame para simular un espejo
            
            # label_width = self._label.winfo_width()
            # label_height = self._label.winfo_height()
            # frame = cv2.resize(frame, (label_width, label_height), interpolation=cv2.INTER_AREA)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Siempre detecta rostros en cada frame para encontrar el más cercano
            faces = self.detector(gray_frame)

            if len(faces) > 0:
                # Encuentra el rostro más grande y asume que es el más cercano
                largest_face = max(faces, key=lambda rect: rect.width() * rect.height())
                # Inicia el seguimiento en el rostro más grande
                self.tracker.start_track(frame, largest_face)
                self.tracking_face = True
                self.scan_effect(frame)  # Aplica el efecto de escaneo al rostro detectado

            if self.tracking_face:
                # Si se está rastreando un rostro, actualiza el tracker
                tracking_quality = self.tracker.update(frame)

                if tracking_quality >= 7:  # Umbral de calidad para el seguimiento
                    tracked_position = self.tracker.get_position()
                    # Dibuja un rectángulo alrededor del rostro rastreado
                    cv2.rectangle(frame, (int(tracked_position.left()), int(tracked_position.top())),
                                (int(tracked_position.right()), int(tracked_position.bottom())), (255, 255, 255), 1)
                    
                else:
                    self.tracking_face = False  # Detiene el seguimiento si la calidad es baja

            img_ = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_)
            imgtk = ImageTk.PhotoImage(image=pil_image)

            self._label.imgtk = imgtk
            self._label.configure(image=imgtk)

            self.most_recent_capture_arr = frame

        except Exception as e:
            print("Error al procesar la imagen:", e)
            #util.msg_box('ERROR', 'Error al procesar la imagen')

        self._label.after(10, self.process_webcam)

        
    def reset_scan_line(self):
        global line_y, direction
        line_y = 0
        direction = 1
        
    def draw_scan_line(self, frame):
        global line_y, direction

        # ajuste de la volicidad de barra
        displacement = 20

        # definir el color de la barra
        neon_color = (127, 255, 0)

        ret, current_frame = self.cap.read()
        current_frame = cv2.flip(current_frame, 1)
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        faces = self.detector(gray_frame)

        if len(faces) == 0:
            line_y = 0
            direction = 1
            return frame

     
        line_y += displacement * direction

        if line_y >= frame.shape[0] or line_y <= 0:
            direction *= -1

      
        line_thickness = 3
        cv2.line(frame, (0, line_y), (frame.shape[1], line_y), neon_color, line_thickness)

        # Verifica si la línea ha alcanzado la parte inferior de la imagen
        if line_y >= frame.shape[0]:
            # Llama a la función de inicio de sesión automáticamente
            self.login()

        return frame
    
    
    def add_scanning_text(self, frame, scanning_text):
        text_size = cv2.getTextSize(scanning_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2  

        text_y_offset = 75  
        text_y = frame.shape[0] - text_y_offset  

        # Definir el color del texto
        text_color = (0, 255, 0)  # Verde

        text_position = (text_x, text_y)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1

        if int(time.time()) % 2 == 0: 
            cv2.putText(frame, scanning_text, text_position, font, font_scale, text_color, font_thickness)

        return frame
    
    def scan_effect(self, frame):
        
        frame = self.draw_scan_line(frame)


        scanning_text = "Escaneando..."
        frame = self.add_scanning_text(frame, scanning_text)

        return frame
    
    # def login(self, rfc_identificado):

    #     label = test(
    #         image=self.most_recent_capture_arr,
    #         model_dir='./resources/anti_spoof_models',
    #         device_id=0
    #     )

    #     if label == 1:
    #         name = util.recognize(self.most_recent_capture_arr, self.db_dir)

    #         if name in ['unknown_person', 'no_persons_found']:
                
    #             entry_type = 'No registrado'
    #             self.msg_box('Ups...', 'Usuario desconocido. \nPor favor, regístrate o intenta nuevamente.', 'error')
    #             self.register_facial_entry(None, entry_type, False)
    #         else:
    #             entry_type = 'Entrada Exitosa'
    #             self.msg_box('Bienvenido de nuevo!', '¡Bienvenido, {}!'.format(name), 'éxito')

    #             success = True if entry_type == 'Entrada Exitosa' else False
    #             self.register_facial_entry(name, entry_type, success)

    #             rfc_identificado = name
    #             self.procesar_rfc_usuario(rfc_identificado)
    #             self.procesar_rfc_usuario(rfc_identificado, tipo='entrada')
           
    #     else:
    #         entry_type = 'Entrada Fallida'
    #         self.msg_box('HEY...', '¡No uses fotos!', 'error')
    #         self.register_facial_entry(None, entry_type, False)
            
    # def logout(self):

    #     label = test(
    #             image=self.most_recent_capture_arr,
    #             model_dir='./resources/anti_spoof_models',
    #             device_id=0
    #             )

    #     if label == 1:

    #         name = util.recognize(self.most_recent_capture_arr, self.db_dir)

    #         if name in ['unknown_person', 'no_persons_found']:
    #             self.msg_box('Ups...', 'Usuario desconocido. \nPor favor, regístrate o intenta nuevamente.', 'error')
    #             self.register_facial_entry(None, entry_type, False)
    #         else:
    #             util.msg_box('Hasta la vista !', 'Adios, {}.'.format(name))
    #             with open(self.log_path, 'a') as f:
    #                 f.write('{},{},out\n'.format(name, datetime.datetime.now()))
    #                 f.close()

    #     else:
    #         util.msg_box('Hey, you are a spoofer!', 'You are fake !')
  
  
    def login(self):
        label = test(
            image=self.most_recent_capture_arr,
            model_dir='./resources/anti_spoof_models',
            device_id=0
        )

        if label == 1:
            rfc = util.recognize(self.most_recent_capture_arr, self.db_dir)

            if rfc in ['unknown_person', 'no_persons_found']:
                self.msg_box('Ups...', 'Error al escenaer el rostro', 'error')
                play_error_escaneo()
                self.register_facial_entry(None, 'No registrado', False)
            else:
                schedule_type = get_employee_schedule_type(self.db, rfc)
                estatus = None

                if schedule_type == 'Abierto':
                    message = add_open_schedule_check(self.db, rfc, "entrada")
                    self.msg_box('Registro de Asistencia', message, 'éxito')
                    if message == f"Entrada registrada con éxito {rfc}. ¡Bienvenido de nuevo!":
                        play_normal_sound()
                    elif message == f"Bienvenido {rfc}, llegaste a tiempo. Asistencia tomada.":
                        play_normal_sound()
                    elif message == f"Hasta luego {rfc}, salida registrada a tiempo.":
                        play_sa_normal()
                elif schedule_type == 'Cerrado':
                    resultado = verificar_y_actualizar_horario_fechas(self.db, rfc)
                    if isinstance(resultado, tuple):
                        estatus, action_type = resultado
                    else:
                        self.msg_box('Error', resultado, 'error')
                    if estatus:
                        status_messages = {
                            "NORMAL": {
                                "entrada": f"Bienvenido {rfc}, llegaste a tiempo, asistencia tomada.",
                                "salida": f"Hasta luego {rfc}, salida registrada a tiempo."
                            },
                            "RETARDO": {
                                "entrada": f"¡CASI! {rfc}, llegaste un poco tarde, asistencia tomada con retardo.",
                                "salida": f"¡CUIDADO! {rfc}, has salido tarde."
                            },
                            "NOTA MALA": {
                                "entrada": f"¡UPSS! {rfc}, esta vez tienes nota mala, llegaste tarde.",
                                "salida": f"¡ALERTA! {rfc}, has salido mucho más tarde de lo previsto."
                            }
                        }
                        message_types = {
                            "NORMAL": "éxito",
                            "RETARDO": "retardo",
                            "NOTA MALA": "fueraderango"
                        }
                        message = status_messages.get(estatus, {}).get(action_type, "Ya escaneado o  fuera de rango.")
                        #ction_config = status_messages.get(estatus, {}).get(action_type, None)
                        print(message)

                        if message == "Ya escaneado o  fuera de rango.":
                            play_ya_scaneado()
                        
                        elif message == f"Bienvenido {rfc}, llegaste a tiempo, asistencia tomada.":
                            play_normal_sound()
                        
                        elif message == f"Hasta luego {rfc}, salida registrada a tiempo.":
                            play_sa_normal()
                        
                        elif message == f"¡CASI! {rfc}, llegaste un poco tarde, asistencia tomada con retardo.":
                            play_retardo_sound()

                        elif message == f"¡CUIDADO! {rfc}, has salido tarde.":
                            play_sa_retardo()

                        elif message == f"¡UPSS! {rfc}, esta vez tienes nota mala, llegaste tarde.":
                            play_nota_mala_sound()

                        elif message == f"¡ALERTA! {rfc}, has salido mucho más tarde de lo previsto.":
                            play_sa_notamala()

                        elif message == "Ya escaneado o  fuera de rango.":
                            play_ya_scaneado()
                        message = status_messages.get(estatus, {}).get(action_type, "Estado no reconocido O fuera de rango.")
                        message_type = message_types.get(estatus, "error")  # Default to "error" if status is unrecognized
                        self.msg_box('Registro de Asistencia', message, message_type)

                entry_success = estatus in ["NORMAL", "RETARDO"]
                entry_type = 'Entrada Exitosa' if entry_success else 'Entrada Fallida'
                self.register_facial_entry(rfc, entry_type, entry_success)

        else:
            self.msg_box('ERROR', 'Error al escanear el', 'error')
            #play_error_escaneo()
            self.register_facial_entry(None, 'Entrada Fallida', False)


 
def create_window():
    global external_process
    
    # Create the main window
    root = tk.Tk()
    root.state('zoomed')  
    root.title("Instituto Tecnológico de Tuxtepec")
    root.attributes('-topmost', True)

    # Get screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()


    window_width = int(screen_width * 0.8)
    window_height = int(screen_height * 0.8)

 
    position_x = int((screen_width - window_width) / 2)
    position_y = int((screen_height - window_height) / 2)


    root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")


    root.grid_rowconfigure(1, weight=1) 
    root.grid_columnconfigure(0, weight=45, minsize=window_width*0.45) 
    root.grid_columnconfigure(1, weight=50, minsize=window_width*0.50) 

   
    header_frame = tk.Frame(root, bg='white', height=50) 
    header_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
    header_frame.grid_propagate(False)

     
    logo_image_left = load_resized_image('RECURSOS/logo_ittux.png', (50, 50))
    logo_image_right = load_resized_image('RECURSOS/LOGO_TECNM.png', (50, 50))

    # Logo izquierdo
    logo_label_left = tk.Label(header_frame, image=logo_image_left, bg='white')
    logo_label_left.pack(side='left', padx=10)

    # Logo derecho
    logo_label_right = tk.Label(header_frame, image=logo_image_right, bg='white')
    logo_label_right.pack(side='right', padx=10)

    # Institute name label - centrado en el medio
    name_label = tk.Label(header_frame, text='TECNOLÓGICO NACIONAL DE MÉXICO  CAMPUS TUXTEPEC ', bg='white', fg='black', font=('Roboto', 20))
    name_label.pack(expand=True)

    def redraw_gradient(canvas, start_color, end_color):
        canvas.delete("gradient") 
        width = canvas.winfo_width()  
        create_gradient(canvas, start_color, end_color, width)  

   
    gradient_canvas = Canvas(header_frame, bg='white', height=10, bd=0, highlightthickness=0)
    gradient_canvas.pack(fill='x', side='bottom')

   
    create_gradient(gradient_canvas, 'green', 'blue', gradient_canvas.winfo_reqwidth())


    gradient_canvas.bind("<Configure>", lambda event, canvas=gradient_canvas, start_color='green', end_color='blue': redraw_gradient(canvas, start_color, end_color))

    logo_label_left.image = logo_image_left
    logo_label_right.image = logo_image_right

    # Central Frame Configuration
    central_frame = tk.Frame(root, bg='white', bd=2, relief='groove')
    central_frame.grid(row=1, column=0, sticky='nswe')
    central_frame.grid_propagate(False)
    central_frame.grid_columnconfigure(0, weight=1)
    central_frame.grid_rowconfigure(0, weight=60, minsize=20)  # Ajusta 'altura_deseada' al valor que prefieras
    central_frame.grid_columnconfigure(0, weight=2, minsize=20)  # Ajusta 'ancho_deseado' al valor que prefieras

    # Frame para la cámara
    top_left_frame = tk.Frame(central_frame, bg='green', bd=2, relief='groove')
    top_left_frame.grid(row=0, column=0, padx=50, pady=50, sticky='nsew')#este frame es el del video ojo
    top_left_frame.grid_propagate(False)

    # Label para mostrar el video de la cámara
    webcam_label = tk.Label(top_left_frame)
    webcam_label.grid(row=0, column=0, sticky="nsew")

    ################################################################

    bottom_left_frame = tk.Frame(central_frame, bg='#EFEFEF', bd=2, relief='groove')
    bottom_left_frame.grid(row=1, column=0, sticky='nswe')
    bottom_left_frame.grid_propagate(False)


    bottom_left_frame.grid_columnconfigure(0, weight=1)


    bottom_left_frame.grid_rowconfigure(0, minsize=60) 
    bottom_left_frame.grid_rowconfigure(1, minsize=30)  
    
    font_style = ('digital-7', 30)  
    time_label = tk.Label(bottom_left_frame, font=font_style, fg='black', bg='#EFEFEF')
    time_label.pack(side='top', fill='x', expand=False, pady=(10, 0))  
    
    date_font_style = ('Helvetica', 18) 
    date_label = tk.Label(bottom_left_frame, font=date_font_style, fg='black', bg='#EFEFEF')
    date_label.pack(side='top', fill='x', expand=True, pady=(5, 10))  

 
    update_time(time_label, root)
    update_date(date_label)

 
    right_frame = tk.Frame(root, bg='white', bd=2, relief='groove')
    right_frame.grid(row=1, column=1, sticky='nswe')
    right_frame.grid_propagate(False)

    right_frame = tk.Frame(root, bg='white', bd=2, relief='groove')
    right_frame.grid(row=1, column=1, sticky='nswe')
    right_frame.grid_columnconfigure(0, weight=1)  

    """# Configura las filas del right_frame para las secciones y los separadores
    right_frame.grid_rowconfigure(0, weight=10)  # 10% altura para la primera sección
    right_frame.grid_rowconfigure(1, weight=1)   # Pequeño peso para el primer separador
    right_frame.grid_rowconfigure(2, weight=55)  # 55% altura para la segunda sección
    right_frame.grid_rowconfigure(3, weight=1)   # Pequeño peso para el segundo separador
    right_frame.grid_rowconfigure(4, weight=10)  # 10% altura para la tercera sección
    right_frame.grid_rowconfigure(5, weight=1)   # Pequeño peso para el tercer separador
    right_frame.grid_rowconfigure(6, weight=25)  # 25% altura para la cuarta sección"""

    # Configuración de la fila para Sección 1
    right_frame.grid_rowconfigure(0, minsize=50, weight=10)  # Tamaño fijo para Sección 1

    # Configuración de la fila para el Separador 1
    right_frame.grid_rowconfigure(1, minsize=2, weight=0)  # Altura fija para el separador

    # Configuración de la fila para Sección 2
    right_frame.grid_rowconfigure(2, minsize=250, weight=55)  # Tamaño fijo para Sección 2

    # Configuración de la fila para el Separador 2
    right_frame.grid_rowconfigure(3, minsize=2, weight=0)  # Altura fija para el separador

    # Configuración de la fila para Sección 3
    right_frame.grid_rowconfigure(4, minsize=50, weight=10)  # Tamaño fijo para Sección 3

    # Configuración de la fila para el Separador 3
    right_frame.grid_rowconfigure(5, minsize=2, weight=0)  # Altura fija para el separador

    # Configuración de la fila para Sección 4
    right_frame.grid_rowconfigure(6, minsize=150, weight=25)  # Tamaño fijo para Sección 4

    # Añade los separadores
    separator1 = ttk.Separator(right_frame, orient='horizontal')
    separator1.grid(row=1, column=0, sticky='ew')
    

    separator2 = ttk.Separator(right_frame, orient='horizontal')
    separator2.grid(row=3, column=0, sticky='ew')

    separator3 = ttk.Separator(right_frame, orient='horizontal')
    separator3.grid(row=5, column=0, sticky='ew')


    section1_frame = tk.Frame(right_frame, bg='#079073') 
    section1_frame.grid(row=0, column=0, sticky='nswe')
    section1_label = tk.Label(section1_frame, text='AVISOS', bg='#079073', fg='black', anchor='center', font=('Roboto', 20))  
    section1_label.pack(expand=True, fill='both')  


    section2_frame = tk.Frame(right_frame, bg='#EFEFEF')  
    section2_frame.grid(row=2, column=0, sticky='nswe')
    #section2_label = tk.Label(section2_frame, text='SIN NOVEDAD', bg='#EFEFEF', fg='black', anchor='center', font=('Roboto', 20))  
    #section2_label.pack(expand=True, fill='both')  


    section3_frame = tk.Frame(right_frame, bg='#CFF2EA') 
    section3_frame.grid(row=4, column=0, sticky='nswe')
    section3_label = tk.Label(section3_frame, text='ORGULLOSANTE TECNM', bg='#CFF2EA', fg='black', anchor='center', font=('Roboto', 20)) 
    section3_label.pack(expand=True, fill='both') 


    section4_frame = tk.Frame(right_frame, bg='#EFEFEF')
    section4_frame.grid(row=6, column=0, sticky='nswe')
    

    section4_frame.grid_columnconfigure(0, weight=1)
    section4_frame.grid_columnconfigure(1, weight=0)  
    section4_frame.grid_columnconfigure(2, weight=1)
    section4_frame.grid_rowconfigure(0, weight=1)


    separator4 = ttk.Separator(section4_frame, orient='vertical')
    separator4.grid(row=0, column=1, sticky='ns')
    
    def on_close():
        global external_process

        if external_process is not None:
             external_process.terminate()
             external_process.wait() 

        app_instance.cap.release()  
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)


    app_instance = App(root, top_left_frame, section2_frame, section4_frame)

    
    app_instance.check_for_messages()
    
    
    


    external_process = subprocess.Popen(["DemoDP4500_k/DemoDP4500/bin/Debug/DemoDP4500.exe", "verificar"])


    root.mainloop()




    

if __name__ == "__main__":
    pygame.mixer.init()
    create_window()