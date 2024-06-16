import tkinter as tk
from tkinter import ttk, Canvas 
from PIL import Image, ImageTk
import datetime  
import dlib
import cv2
import os
import util
from register_user import RegisterUserApp
from test import test
import time
import socket
import threading
# ------------------------------------ AGREGAR ESTAS LIBRERIAS ------------------------------------#
import queue
import uuid 
from mongo_connection import add_open_schedule_check, get_db, get_employee_schedule_type, get_info, get_admin_message_by_rfc, update_entry_by_rfc, verificar_y_actualizar_horario_fechas



line_y = 0
direction = 1  

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

    canvas.lower("gradient")  # Lower the gradient lines below any other items

# Función para cargar y redimensionar una imagen
def load_resized_image(path, size):
    # Open the image and resize it
    image = Image.open(path)
    image = image.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(image)

def update_time(time_label, root):
    # Get the current time and format it
    current_time = datetime.datetime.now().strftime('%I:%M:%S %p')
    # Update the time_label with the current time
    time_label.config(text=current_time)
    # Schedule the update_time function to be called after 1000ms (1 second)
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
   
    day_of_week = datetime.datetime.now().strftime("%A")
    # Obtiene la fecha actual sin el día de la semana
    date_str = datetime.datetime.now().strftime("%d/%m/%Y").upper()
    # Usa el mapeo para obtener el día de la semana en español
    day_of_week_es = dias_espanol[day_of_week]
    # Formatea la fecha completa en español
    current_date = f"{day_of_week_es}\n\n{date_str}"
    # Actualiza date_label con la fecha actual en español
    date_label.config(text=current_date)
    
class App:
    def __init__(self, parent_frame, section2_frame, section4_frame):
        self.detector = dlib.get_frontal_face_detector()
        self.tracker = dlib.correlation_tracker()
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

        # Carga y define los labels de imagen dentro del constructor de la clase
        resized_image1 = load_resized_image('RECURSOS/H.png', (90, 100))
        self.image_label1 = tk.Label(self.section4_frame, image=resized_image1, bg='#D3D3D3')
        self.image_label1.grid(row=0, column=0, sticky='nswe')
        self.image_label1.image = resized_image1  # Guarda una referencia a la imagen

        resized_image2 = load_resized_image('RECURSOS/R.png', (90, 90))
        self.image_label2 = tk.Label(self.section4_frame, image=resized_image2, bg='#D3D3D3')
        self.image_label2.grid(row=0, column=2, sticky='nswe')
        self.image_label2.image = resized_image2  # Guarda una referencia a la imagen
        
        self.db_dir = './imagenes_pickle'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.log_path = './log.txt'
        self.most_recent_capture_arr = None

        # ------------------------------------ PARA AVISOS TRABAJADOR 2 MODULOS ------------------------------------ #

    def register_facial_entry(self, name, entry_type, success):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = "exitoso" if success else "fallido"
        entry_id = str(uuid.uuid4())
        log_entry = f"{timestamp} - ID: {entry_id}, Método: Reconocimiento Facial, Nombre: {name}, Tipo: {entry_type}, Resultado: {result}\n"

        with open(self.log_path, 'a') as f:
            f.write(log_entry)
        
        # Comprobar si el nombre (que es el RFC) tiene un mensaje de administrador asociado
        admin_message = get_admin_message_by_rfc(self.db, name)
        if admin_message and admin_message != "No se encontró el RFC en la base de datos." and not admin_message.startswith("Error"):
            self.show_admin_message(admin_message)

    def show_admin_message(self, message):
        """
        Muestra un mensaje de administrador en una ventana emergente que se ajusta al tamaño del mensaje
        y se cierra automáticamente después de 5 segundos.
        """
        top = tk.Toplevel(self.main_frame)
        top.title("Mensaje del Administrador")

        # Crear un label con el mensaje y empaquetarlo con un poco de padding
        msg_label = tk.Label(top, text=message, font=('Arial', 12), wraplength=350)  # Ajusta wraplength según lo necesario
        msg_label.pack(pady=20, padx=20, expand=True)

        # Ajusta la ventana para que se centre sobre la ventana principal
        top.transient(self.main_frame)  # Hace que la ventana flotante esté vinculada a la ventana principal
        top.grab_set()  # Evita que se interactúe con la ventana principal mientras esta esté abierta

        # No se especifica geometry() para que se ajuste al contenido automáticamente
        top.focus_force()  # Pone el foco en la ventana emergente

        # Programa el cierre automático de la ventana después de 5000 milisegundos (5 segundos)
        top.after(5000, top.destroy)

    # ------------------------------------ TERMINA AVISOS TRABAJADOR ------------------------------------ #

    # ------------------------------------ PARA AVISOS GENERALES 1 MODULO -------------------------------- #

    def update_section2(self):
        try:
            # Intenta obtener la información del campo específico
            info = get_info(self.db, 'avisos_generales')
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
        # Configuración del servidor de socket aquí
        threading.Thread(target=self.init_socket_server, daemon=True).start()
    def init_socket_server(self):
        # Inicia el servidor de socket aquí y maneja los mensajes
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
            servidor.bind(("localhost", 12345))
            servidor.listen()
            while True:
                conexion, direccion = servidor.accept()
                threading.Thread(target=self.handle_client, args=(conexion, direccion), daemon=True).start()
                
    def handle_client(self, conexion, direccion):
        toque_contador = 0  # Contador para los toques en el lector
        try:
            while True:
                datos = conexion.recv(1024)
                if not datos:
                    break  # Cliente cerró la conexión
                mensaje_completo = datos.decode("ascii").strip()
                # Verificar si el mensaje es un comando para cerrar la conexión
                if mensaje_completo == "CERRAR_CONEXION":
                    print(f"Cerrando conexión con {direccion}")
                    break
                # Si el mensaje indica que el lector fue tocado, incrementa el contador
                if mensaje_completo == "El lector fue tocado":
                    toque_contador += 1
                    # Si el lector fue tocado dos veces sin captura, asume un fallo
                    if toque_contador >= 2:
                        self.message_queue.put("No ha podido tomar su asistencia")
                        toque_contador = 0  # Restablece el contador
                else:
                    # Si se recibe otro tipo de mensaje, procesa como de costumbre y restablece el contador
                    self.message_queue.put(mensaje_completo)
                    toque_contador = 0
        except Exception as e:
            print(f"Error al manejar al cliente {direccion}: {e}")
        finally:
            conexion.close() 
                
    def mostrar_usuario_no_registrado(self):
            # Limpia la sección antes de mostrar el mensaje de error
            for widget in self.section2_frame.winfo_children():
                widget.destroy()

            # Obtén la hora, día y fecha actuales
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            current_day = dias_espanol.get(datetime.datetime.now().strftime("%A"), '')
            current_date = datetime.datetime.now().strftime("%d / %m / %Y")

            # Configura el mensaje de error con la hora, fecha y día incluidos
            error_bg_color = '#FFCCCC'  # Un color de fondo rojo claro para indicar un error
            error_message = f"Usuario no registrado. Por favor, regístrese o intente nuevamente.\n\nHora: {current_time}\nDía: {current_day}\nFecha: {current_date}"

            # Crea un contenedor para el mensaje de error
            error_container = tk.Frame(self.section2_frame, bg=error_bg_color, borderwidth=2, relief="groove")
            error_container.pack(expand=False, fill='both', padx=10, pady=10)
            error_container.pack_propagate(False)  # Evita que el contenedor cambie de tamaño según su contenido
            error_container.place(relx=0.5, rely=0.5, anchor='center', width=500, height=300)

            # Crea y muestra el mensaje de error dentro del contenedor
            error_label = tk.Label(error_container, text=error_message, bg=error_bg_color, fg='black', font=('Arial', 14), wraplength=480)
            error_label.pack(padx=20, pady=20)

            # Programa la restauración del contenido original de section2_frame después de 5 segundos
            self.section2_frame.after(5000, self.restore_section2_content)


        
    def check_for_messages(self):
    # Verifica si hay mensajes nuevos en la cola y actúa en consecuencia
        while not self.message_queue.empty():
            mensaje_completo = self.message_queue.get_nowait()
            print(f"Mensaje recibido: {mensaje_completo}")

            partes = mensaje_completo.split(": ")
            accion = partes[0]
            idHuella = partes[1] if len(partes) > 1 else ""

            # Define el mapa de colores para cada acción
            color_map = {
                'Asistencia tomada': '#008000',  # Verde
                'Escaneo fallido': '#FF0000',  # Rojo
            }

            # Determina el color basado en la acción
            background_color = color_map.get(accion, '#D3D3D3')  # Gris como color por defecto

            # Aplica el color al label que corresponde antes de realizar la acción
            # Asumiendo que tienes un label específico para mostrar estos mensajes
            self.image_label1.config(bg=background_color)


            # Realiza la acción correspondiente
            if accion == "Asistencia tomada":
                self.registrar_asistencia(idHuella)
            elif accion == "Escaneo fallido":
                self.mostrar_error()
            else:
                print("Acción no reconocida.")

            
        self.main_frame.after(100, self.check_for_messages)
        
    def registrar_asistencia(self, idHuella):
        # Actualiza la UI con un mensaje de asistencia tomada
        mensaje = f"Asistencia registrada con éxito para {idHuella}."
        self.msg_box('Asistencia Tomada', mensaje, 'éxito')
        
        

    def mostrar_error(self):
        # Actualiza la UI con un mensaje de error de escaneo
        self.msg_box('Error', 'El escaneo de la huella dactilar ha fallado.', 'error')


    def msg_box(self, title, message, message_type):
        # Limpia la sección 2 antes de mostrar un nuevo mensaje
        for widget in self.section2_frame.winfo_children():
            widget.destroy()
            
        # Configura el color de fondo según el tipo de mensaje
        color_map = {
            'escaneando': '#D3D3D3',  # Gris
            'error': '#FF0000',  # Rojo
            'éxito': '#008000',  # Verde
        }
        
        background_color = color_map.get(message_type, '#D3D3D3')  # Color por defecto

        # Cambia el color de fondo de los Labels en section4_frame
        self.image_label2.config(bg=background_color)

        # Crear el contenedor para los mensajes dentro de section2_frame
        message_container = tk.Frame(self.section2_frame, bg='white', borderwidth=2, relief="groove")
        message_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Crear la etiqueta para mostrar el mensaje
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        current_day = dias_espanol.get(datetime.datetime.now().strftime("%A"), '')
        current_date = datetime.datetime.now().strftime("%d / %m / %Y")
        full_message = f"{title}\n{message}\n\nHora: {current_time}\nDía: {current_day}\nFecha: {current_date}"
        message_label = tk.Label(message_container, text=full_message, bg='white', font=('Arial', 18))
        message_label.pack(padx=20, pady=20)

        # Programa la función para restablecer el color de fondo de la imagen después de 5 segundos
        self.image_label2.after(5000, lambda: self.image_label2.config(bg='#D3D3D3'))  # Asume que '#D3D3D3' es el color original

    def add_webcam(self, label):
        self.cap = cv2.VideoCapture(0)
        # Establece una resolución más baja
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # Ajusta los FPS si es necesario
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self._label = label
        self.process_webcam()


    def process_webcam(self):
        try:
            ret, frame = self.cap.read()
            frame = cv2.flip(frame, 1)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray_frame)
            

            if len(faces) > 0:
          
                self.scan_effect(frame)

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

        # aqui se puede ajustar la velocidad de la barra 
        displacement = 23  

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
        text_y = frame.shape[0] - text_y_offset  # Mueve el texto más arriba

        # Definir el color del texto
        text_color = (0, 255, 0)  # Verde

        text_position = (text_x, text_y)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1

        if int(time.time()) % 2 == 0:  # Parpadeo cada segundo
            cv2.putText(frame, scanning_text, text_position, font, font_scale, text_color, font_thickness)

        return frame
    
    def scan_effect(self, frame):
        
        frame = self.draw_scan_line(frame)


        scanning_text = "Escaneando..."
        frame = self.add_scanning_text(frame, scanning_text)

        return frame
    
    def login(self):
        label = test(
            image=self.most_recent_capture_arr,
            model_dir='./resources/anti_spoof_models',
            device_id=0
        )

        message = "Acción no completada"  # Inicializa la variable message con un valor predeterminado

        if label == 1:
            rfc = util.recognize(self.most_recent_capture_arr, self.db_dir)  # Reconocimiento devuelve el RFC

            if rfc in ['unknown_person', 'no_persons_found']:
                self.msg_box('Ups...', 'Usuario desconocido. \nPor favor, regístrate o intenta nuevamente.', 'error')
                self.register_facial_entry(None, 'No registrado', False)
                message = "Usuario no registrado."  # Actualiza la variable message aquí
            else:
                # Obtener el tipo de horario del empleado
                schedule_type = get_employee_schedule_type(self.db, rfc)

                if schedule_type == 'abierto':
                    message = add_open_schedule_check(self.db, rfc, "entrada")  # Suponiendo que esta función retorna un mensaje
                elif schedule_type == 'Cerrado':
                    message = verificar_y_actualizar_horario_fechas(self.db, rfc)  # Asegúrate que esta función retorna un mensaje

                entry_success = "Exitosa" in message or "NORMAL" in message or "RETARDO" in message
                entry_type = 'Entrada Exitosa' if entry_success else 'Entrada Fallida'
                self.register_facial_entry(rfc, entry_type, entry_success)

            self.msg_box('Registro de Asistencia', message, 'éxito' if entry_success else 'éxito')  # Usa message y entry_success fuera del bloque if-else

        else:
            self.msg_box('HEY...', '¡No uses fotos!', 'error')
            self.register_facial_entry(None, 'Entrada Fallida', False)

        return message  # Devuelve la respuesta para posible depuración o uso adicional

            
        
def create_window():
    
    # Create the main window
    root = tk.Tk()
    root.state('zoomed')  # Esto maximiza la ventana en Windows.
    root.title("Instituto Tecnológico de Tuxtepec")

    # Get screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate window width and height as a proportion of the screen size
    window_width = int(screen_width * 0.8)
    window_height = int(screen_height * 0.8)

    # Calculate position x and y coordinates to center the window on the screen
    position_x = int((screen_width - window_width) / 2)
    position_y = int((screen_height - window_height) / 2)

    # Set the size of the window and position it on the screen
    root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    # Configure the layout with Grid
    root.grid_rowconfigure(1, weight=1)  # Give a weight to the main content row
    root.grid_columnconfigure(0, weight=45, minsize=window_width*0.45)  # 45% weight to the left column, minsize set
    root.grid_columnconfigure(1, weight=50, minsize=window_width*0.50)  # 55% weight to the right column, minsize set

    # Header Frame Configuration
    header_frame = tk.Frame(root, bg='white', height=50)  # Fondo blanco para el encabezado
    header_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
    header_frame.grid_propagate(False)

    # Carga y redimensiona las imágenes para los logos
    logo_image_left = load_resized_image('RECURSOS/logo_ittux.png', (50, 50))
    logo_image_right = load_resized_image('RECURSOS/LOGO_TECNM.png', (50, 50))

    # Logo izquierdo
    logo_label_left = tk.Label(header_frame, image=logo_image_left, bg='white')
    logo_label_left.pack(side='left', padx=10)

    # Logo derecho
    logo_label_right = tk.Label(header_frame, image=logo_image_right, bg='white')
    logo_label_right.pack(side='right', padx=10)

    # Institute name label - centrado en el medio
    name_label = tk.Label(header_frame, text='TECNOLOGICO NACIONAL DE MEXICO  CAMPUS TUXTEPEC ', bg='white', fg='black', font=('Roboto', 20))
    name_label.pack(expand=True)

    def redraw_gradient(canvas, start_color, end_color):
        canvas.delete("gradient")  # Elimina el degradado anterior
        width = canvas.winfo_width()  # Obtiene el nuevo ancho del canvas
        create_gradient(canvas, start_color, end_color, width)  # Dibuja un nuevo degradado

    # Lugar donde creas y configuras tu Canvas para el degradado
    gradient_canvas = Canvas(header_frame, bg='white', height=10, bd=0, highlightthickness=0)
    gradient_canvas.pack(fill='x', side='bottom')

    # Inicialmente dibuja el degradado
    create_gradient(gradient_canvas, 'green', 'blue', gradient_canvas.winfo_reqwidth())

    # Asocia el redibujado del degradado con el evento de redimensionamiento del canvas
    gradient_canvas.bind("<Configure>", lambda event, canvas=gradient_canvas, start_color='green', end_color='blue': redraw_gradient(canvas, start_color, end_color))

    # Guarda una referencia a las imágenes para evitar que sean recolectadas por el recolector de basura
    logo_label_left.image = logo_image_left
    logo_label_right.image = logo_image_right

    # Central Frame Configuration
    central_frame = tk.Frame(root, bg='white', bd=2, relief='groove')
    central_frame.grid(row=1, column=0, sticky='nswe')
    central_frame.grid_propagate(False)
    central_frame.grid_columnconfigure(0, weight=1)  # Configure grid inside left frame
    central_frame.grid_rowconfigure(0, weight=90)  # 65% weight to the top left frame
    central_frame.grid_rowconfigure(1, weight=10)  # 35% weight to the bottom left frame

    # Frame para la cámara
    top_left_frame = tk.Frame(central_frame, bg='green', bd=2, relief='groove')
    top_left_frame.grid(row=0, column=0, sticky='nswe')
    top_left_frame.grid_propagate(False)
    
     # Label para mostrar el video de la cámara
    webcam_label = tk.Label(top_left_frame)
    webcam_label.pack(expand=True, fill=tk.BOTH)
    ################################################################

    bottom_left_frame = tk.Frame(central_frame, bg='#EFEFEF', bd=2, relief='groove')
    bottom_left_frame.grid(row=1, column=0, sticky='nswe')
    bottom_left_frame.grid_propagate(False)

    # Configuración para usar 'grid' en lugar de 'pack'
    bottom_left_frame.grid_columnconfigure(0, weight=1)

    # Establecer minsize para las filas de los labels
    bottom_left_frame.grid_rowconfigure(0, minsize=60)  # Ajusta este valor según el tamaño de la fuente del reloj
    bottom_left_frame.grid_rowconfigure(1, minsize=30)  # Ajusta este valor según el tamaño de la fuente de la fecha
    
    font_style = ('digital-7', 30)  # Define the font and size for labels
    time_label = tk.Label(bottom_left_frame, font=font_style, fg='black', bg='#EFEFEF')
    time_label.pack(side='top', fill='x', expand=False, pady=(10, 0))  
    
    date_font_style = ('Helvetica', 18)  # Different font size for date
    date_label = tk.Label(bottom_left_frame, font=date_font_style, fg='black', bg='#EFEFEF')
    date_label.pack(side='top', fill='x', expand=True, pady=(5, 10))  # Añade espacio en la parte superior e inferior

    # Initial update of time and date
    update_time(time_label, root)
    update_date(date_label)

    # Frame for the right side
    right_frame = tk.Frame(root, bg='white', bd=2, relief='groove')
    right_frame.grid(row=1, column=1, sticky='nswe')
    right_frame.grid_propagate(False)

    right_frame = tk.Frame(root, bg='white', bd=2, relief='groove')
    right_frame.grid(row=1, column=1, sticky='nswe')
    right_frame.grid_columnconfigure(0, weight=1)  # Asegúrate de que el contenido se expanda para llenar el ancho

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

    # Sección 1 - 10% altura
    section1_frame = tk.Frame(right_frame, bg='#079073')  # Usa el color HTML directamente
    section1_frame.grid(row=0, column=0, sticky='nswe')
    section1_label = tk.Label(section1_frame, text='AVISOS', bg='#079073', fg='black', anchor='center', font=('Roboto', 20))  # Texto centrado
    section1_label.pack(expand=True, fill='both')  # El Label se expande y llena el Frame


    # ------------------------------------ REALIZAR ESTE CAMBIO -------------------------------- #
    # Sección 2 - 55% altura
    section2_frame = tk.Frame(right_frame, bg='#EFEFEF')  # Usa el color HTML directamente
    section2_frame.grid(row=2, column=0, sticky='nswe')
    """section2_label = tk.Label(section2_frame, text='SIN NOVEDAD', bg='#EFEFEF', fg='black', anchor='center', font=('Roboto', 20))  # Texto centrado
    section2_label.pack(expand=True, fill='both')"""  # El Label se expande y llena el Frame

    # Sección 3 - 10% altura
    section3_frame = tk.Frame(right_frame, bg='#CFF2EA')  # Usa el color HTML directamente
    section3_frame.grid(row=4, column=0, sticky='nswe')
    section3_label = tk.Label(section3_frame, text='ORGULLOSANTE TECNM', bg='#CFF2EA', fg='black', anchor='center', font=('Roboto', 20))  # Texto centrado
    section3_label.pack(expand=True, fill='both')  # El Label se expande y llena el Frame

    # Sección 4 - 25% altura, dividida en dos partes iguales por una línea vertical
    section4_frame = tk.Frame(right_frame, bg='#EFEFEF')
    section4_frame.grid(row=6, column=0, sticky='nswe')
    
    # Configura las columnas y filas para el layout de la sección 4
    section4_frame.grid_columnconfigure(0, weight=1)
    section4_frame.grid_columnconfigure(1, weight=0)  # Configurar la columna del separador sin expandir
    section4_frame.grid_columnconfigure(2, weight=1)
    section4_frame.grid_rowconfigure(0, weight=1)

    # Separador vertical en su propia columna
    separator4 = ttk.Separator(section4_frame, orient='vertical')
    separator4.grid(row=0, column=1, sticky='ns')
    
    def on_close():
        app_instance.cap.release()  # Asumiendo que cap es accesible aquí
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)


    app_instance = App(top_left_frame, section2_frame, section4_frame)
    app_instance.check_for_messages()
    #app_instance.daily_update()

    # Run the main loop
    root.mainloop()

if __name__ == "__main__":
    create_window()
