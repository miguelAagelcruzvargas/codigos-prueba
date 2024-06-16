import os.path
import datetime
from time import strftime, sleep

import tkinter as tk
import cv2
import dlib
from PIL import Image, ImageTk

import util
from test import test
from register_user import RegisterUserApp

class App:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.tracker = dlib.correlation_tracker()
       
        self.main_window = tk.Tk()
        self.main_window.geometry("1170x720+350+100")
        
        #frame
        self.frame_inferior = tk.Frame(self.main_window, bg='spring green')
        self.frame_inferior.place(x=0, y=530, width=749, height=190)
        
        ################ label para imagenes ####################
        """
        Documentacion
        
        se cargan las imagenes necesarias las cuales indicaran el estado
        o accion que se relaice en el sistema 
        
        inactivo.png (imagen mostrada por defecto) cuando el sistema no 
        esta realizando ninguna accion
        
        correcto.png: se muestra cuando el escaneo se realizó exitosamente
        
        fallido.png: se muestra cuando el escaneo no se realizó exitosamente
        
        """
        self.image1 = Image.open("imagenes_ui/inactivo.png")  
        self.image1 = self.image1.resize((75, 75)) 

        self.image2 = Image.open("imagenes_ui/correcto.png")  
        self.image2 = self.image2.resize((75, 75)) 
        
        self.image3 = Image.open("imagenes_ui/fallido.png")  
        self.image3 = self.image3.resize((75, 75)) 
        
        # label imagen 1
        self.label_image1 = tk.Label(self.frame_inferior, bg='spring green')
        self.label_image1.pack(side='right', pady=50, padx=15) 
        
        # Mostrar la imagen inactiva por defecto
        self.photo_image1 = ImageTk.PhotoImage(self.image1)
        self.label_image1.config(image=self.photo_image1)
        
        # Añadir atributos para las otras imágenes
        self.photo_image2 = ImageTk.PhotoImage(self.image2)
        self.photo_image3 = ImageTk.PhotoImage(self.image3)

        self.logged_in = False
        
        ################# IMGANEN 2 ###################
          
        self.huella = Image.open("imagenes_ui/H_inactiva.png")   
        self.huella = self.huella.resize((75, 75)) 
        
        # label imagen 2
        self.label_huella = tk.Label(self.frame_inferior, bg='spring green')
        self.label_huella.pack(side='right', pady=50, padx=70)
        
        self.photo_huella = ImageTk.PhotoImage(self.huella)
        self.label_huella.config(image=self.photo_huella)

        ################### RELOJ Y FECHA #############
        
        # configuraciones para el reloj
        self.reloj_label = tk.Label(self.frame_inferior, fg='purple1', bg='spring green', font=('Radioland', 40))
        self.reloj_label.pack(side='top', pady=5, padx=2, anchor='w')
        
        #configuraciones para el dia
        self.texto_dia = tk.Label(self.frame_inferior, fg='white', bg='spring green', font=('Lucida Calligraphy', 15))
        self.texto_dia.pack(side='top', padx=65, anchor='w')
        
         #configuraciones para la fecha
        self.texto_fecha = tk.Label(self.frame_inferior, fg='black', bg='spring green', font=('Comic Sans MS', 18, 'bold'))
        self.texto_fecha.pack(side='top', padx=30, anchor='w')
        
        self.actualizar_reloj()

        # frame para los avisos
        self.frame_info = tk.Frame(self.main_window, bg='light blue')
        self.frame_info.place(x=750, y=30, width=400, height=690)
        
        # título "AVISOS"
        titulo_label = tk.Label(self.frame_info, text="AVISOS", font=('Arial', 25), bg='light blue')
        titulo_label.pack(side='top', pady=5)
        
        #label del boton  login
        self.login_button_main_window = util.get_button(self.frame_info, 'Asistencia', 'green', self.login)
        self.login_button_main_window.pack(side='bottom', pady=5)
        
        #frame
        self.frame_camara = tk.Frame(self.main_window, bg='black', bd=3, highlightbackground="black")
        self.frame_camara.place(x=25, y=30, width=725, height=500)
       
        #label para la camara
        self.webcam_label = util.get_img_label(self.frame_camara)
        # el color el solo para saber el tamaño del label
        
        self.webcam_label.configure(bg='green')
        self.webcam_label.pack(fill=tk.BOTH, padx=40, pady=10)
        
        # self.webcam_label = util.get_img_label(self.main_window)
        # self.webcam_label.place(x=25, y=30, width=700, height=500)

        # self.add_webcam(self.webcam_label)
        self.add_webcam(self.webcam_label)

        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

        self.log_path = './log.txt'
        self.most_recent_capture_arr = None

    def add_webcam(self, label):
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(1)

        self._label = label
        self.process_webcam()

    def process_webcam(self):
        try:
             
            ret, frame = self.cap.read()
            frame = cv2.flip(frame, 1)

            # Convertir el marco a escala de grises para la detección de rostros
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detectar rostros en la imagen en escala de grises
            faces = self.detector(gray_frame)

            # Si se detectan rostros, seleccionar el más cercano para seguir
            if len(faces) > 0:
                # Calcular la distancia de los rostros detectados al centro de la imagen
                center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
                distances = [abs(face.left() + face.right() - center_x * 2 + face.top() + face.bottom() - center_y * 2) for face in faces]
                
                # Obtener el índice del rostro más cercano al centro
                closest_face_index = distances.index(min(distances))
                face = faces[closest_face_index]

                # Obtener las coordenadas del rectángulo del rostro más cercano
                x, y, w, h = face.left(), face.top(), face.width(), face.height()

                # Inicializar el rastreador con las coordenadas del rostro más cercano
                self.tracker.start_track(frame, dlib.rectangle(x, y, x+w, y+h))

                # Actualizar la posición del rastreador en el siguiente fotograma
                self.tracker.update(frame)

                # Obtener las nuevas coordenadas del rectángulo del rostro
                pos = self.tracker.get_position()
                x, y, w, h = int(pos.left()), int(pos.top()), int(pos.width()), int(pos.height())

                # Dibujar el rectángulo del rostro más cercano en el marco
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Convertir la imagen al formato correcto para mostrarla en Tkinter
            img_ = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_)
            imgtk = ImageTk.PhotoImage(image=pil_image)

            # Actualizar la etiqueta con la imagen de la cámara web
            self._label.imgtk = imgtk
            self._label.configure(image=imgtk)
            
            self.most_recent_capture_arr = frame
            
        
        except Exception as e:
            print("Error al procesar la imagen:", e)
            util.msg_box('ERROR', 'Error al procesar la imagen')
             
        self._label.after(20, self.process_webcam)

    # funcion para el login (funcion del spoofing)
    def login(self):
        label = test(
            image=self.most_recent_capture_arr,
            model_dir='./resources/anti_spoof_models',
            device_id=0
        )

        if label == 1:
            name = util.recognize(self.most_recent_capture_arr, self.db_dir)

            if name in ['unknown_person', 'no_persons_found']:
                self.update_login_status(False)
                util.msg_box('Ups...', 'Usuario desconocido. Por favor registrate o intenta nuevamente.')
                
            else:
                self.update_login_status(True)
                
                util.msg_box('Bienvenido de nuevo!', 'Bienvenido, {}.'.format(name))
                
                with open(self.log_path, 'a') as f:
                    f.write('{},{},in\n'.format(name, datetime.datetime.now()))
                    f.close()
                
                
                self.main_window.after(2000, self.force_inactive_status)
               
        else:
            
            self.update_login_status(False)
            
            util.msg_box('NO NOS PUEDES ENGAÑAR!', 'No uses fotos !')
            
            
    def force_inactive_status(self):
            # Cambiar a inactivo solo si no se ha iniciado sesión
            self.label_image1.configure(image=self.photo_image1)

    def update_login_status(self, logged_in):
        
        self.logged_in = logged_in
 
        if logged_in:
            # Mostrar imagen de correcto
              self.label_image1.configure(image=self.photo_image2)
             
        else:
            # Mostrar imagen de fallido
            self.label_image1.configure(image=self.photo_image3)
        
        if not logged_in:
           self.main_window.after(2000, self.reset_login_status)
   
    def reset_login_status(self):
        if not self.logged_in:
            # Mostrar imagen inactivo
            self.label_image1.configure(image=self.photo_image1)
        
    # funcion para llamar a las personas registradas 
    def register_new_user(self):
        register_app = RegisterUserApp()
        
    # funcion para actualizar el reloj, dia y fecha
    def actualizar_reloj(self):
        hora_actual = strftime('%H:%M:%S')
        dia = strftime('%A')
        fecha = strftime('%d / %m / %y')

        if dia == 'Monday':
            dia = 'Lunes'
        elif dia == 'Tuesday':
            dia = 'Martes'
        elif dia == 'Wednesday':
            dia = 'Miércoles'
        elif dia == 'Thursday':
            dia = 'Jueves'
        elif dia == 'Friday':
            dia = 'Viernes'
        elif dia == 'Saturday':
            dia = 'Sábado'
        elif dia == 'Sunday':
            dia = 'Domingo'

        self.reloj_label.config(text=hora_actual)
        self.texto_dia.config(text=dia)
        self.texto_fecha.config(text=fecha)

        self.reloj_label.after(1000, self.actualizar_reloj)

    def start(self):
        try:
            self.main_window.mainloop()
        except Exception as e:
            print("Error al iniciar la aplicación:", e)
            util.msg_box('ERROR', 'Error al iniciar la aplicación')


if __name__ == "__main__":
    app = App()
    app.start()
