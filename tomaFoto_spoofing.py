import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from tkinter import messagebox
import dlib
import pickle
import re
import face_recognition
import numpy as np

from test import test  

def cargar_etiquetas():
    etiquetas_utilizadas = {}
    try:
        with open("etiquetas.txt", "r") as file:
            for line in file:
                etiqueta, numero = line.strip().split(":")
                etiquetas_utilizadas[etiqueta] = int(numero)
    except FileNotFoundError:
        pass
    return etiquetas_utilizadas

def guardar_etiquetas(etiquetas_utilizadas):
    etiquetas_actuales = cargar_etiquetas()
    etiquetas_actuales.update(etiquetas_utilizadas)
    with open("etiquetas.txt", "w") as file:
        for etiqueta, numero in etiquetas_actuales.items():
            file.write(f"{etiqueta}:{numero}\n")

def guardar_nueva_imagen(etiqueta):
    etiquetas_utilizadas = cargar_etiquetas()
    if etiqueta in etiquetas_utilizadas:
        nuevo_numero = etiquetas_utilizadas[etiqueta] + 1
    else:
        nuevo_numero = 1
    etiquetas_utilizadas[etiqueta] = nuevo_numero
    guardar_etiquetas(etiquetas_utilizadas)
    return nuevo_numero

# def get_button(window, text, color, command, fg='white'):
#     button = tk.Button(
#                         window,
#                         text=text,
#                         activebackground="black",
#                         activeforeground="white",
#                         fg=fg,
#                         bg=color,
#                         command=command,
#                         height=2,
#                         width=20,
#                         font=('Helvetica bold', 20)
#                     )
#     return button

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

class App:
    def __init__(self, window):
        self.window = window
        self.window.bind('<ButtonPress-1>', self.start_drag)
        self.window.bind('<ButtonRelease-1>', self.stop_drag)
        self.window.bind('<B1-Motion>', self.on_drag)
        self.etiquetas_utilizadas = cargar_etiquetas()
        self.window.overrideredirect(True)
        self.window.configure(bg='mint cream')

        style = ttk.Style()

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 640
        window_height = 580
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.attributes('-topmost', True)

        self.title_label = tk.Label(window, text="Sistema de Fotos", font=('Arial', 19, 'bold'), bg='mint cream')
        self.title_label.pack(side=tk.TOP, pady=3)

        self.video_source =  0 #"http://192.168.1.2:8080/video"  # URL de la cámara IP
        self.vid = cv2.VideoCapture(self.video_source)
        max_width = self.get_max_resolution_width()
        max_height = self.get_max_resolution_height()
        
        if max_width > 0 and max_height > 0:
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, max_width)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, max_height)
            print(f"Resolución máxima establecida: {max_width}x{max_height}")
        else:
            print("No se pudieron obtener las resoluciones máximas admitidas.")
            
        self.canvas = tk.Canvas(window, width=640, height=480, bg='black') 
        self.canvas.pack()
        
        self.initial_btn_color = 'green'
        
        self.btn_capture = tk.Button(window, text="Capturar", width=10, command=self.capture,  bg=self.initial_btn_color
                                     , fg='white', font=('Arial', 12), bd=0, relief=tk.RAISED , borderwidth=4, cursor="hand2")
        
        self.btn_capture.pack(side=tk.LEFT, padx=10, pady=10)

        self.lbl_etiqueta = tk.Label(window,bg='mint cream', text="RFC:", font=('Arial', 12,'bold'))
        self.lbl_etiqueta.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        self.entry_etiqueta = tk.Entry(window, font=('Arial', 12),highlightbackground="black",highlightthickness=1,selectbackground="blue")
        self.entry_etiqueta.pack(side=tk.LEFT, pady=10)

        self.btn_exit = tk.Button(window, text="Exit", width=10, command=self.confirm_exit, bg='red', fg='white', font=('Arial'
        , 12), bd=0, relief=tk.RAISED , borderwidth=4, cursor="hand2")
        self.btn_exit.pack(side=tk.RIGHT, padx=10, pady=10)
        self.delay = 10

        self.contador = 0
        self.prev_faces = []

        self.update()

        self.directoriorostros = 'rostros_capturados'
        if not os.path.exists(self.directoriorostros):
            os.makedirs(self.directoriorostros)

        self.directorio_pickle = 'imagenes_pickle'
        if not os.path.exists(self.directorio_pickle):
            os.makedirs(self.directorio_pickle)

        self.x = 0
        self.y = 0

        self.window.bind('<ButtonPress-1>', self.start_drag)
        self.window.bind('<ButtonRelease-1>', self.stop_drag)
        self.window.bind('<B1-Motion>', self.on_drag)
    
    def get_max_resolution_width(self):
        return int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    def get_max_resolution_height(self):
        return int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
    def confirm_exit(self):
        confirm = messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir de la aplicación?")
        if confirm:
            if self.vid.isOpened():
                self.vid.release()
            self.window.quit()

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)
            
            for face in faces:
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                
                expand_x = int(0.1 * w)
                expand_y = int(0.1 * h)
                
                x = max(0, x - expand_x)
                y = max(0, y - expand_y)
                w += 2 * expand_x
                h += 2 * expand_y
                
                w = min(frame.shape[1] - x, w)
                h = min(frame.shape[0] - y, h)

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)

            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

            self.window.after(self.delay, self.update)

    def validar_rfc(self, rfc):
        return bool(re.match(r'^[A-Za-z0-9]{13}$', rfc))

    def rfc_existe(self, rfc):
        return os.path.exists(os.path.join(self.directoriorostros, f'{rfc}.jpg'))

    def capture(self):
        ret, frame = self.vid.read()

        frame = cv2.flip(frame, 1)
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)

            if len(faces) > 0:
                face = faces[0]
                x, y, w, h = face.left(), face.top(), face.width(), face.height()

                landmarks = predictor(gray, face)

                scale_factor_x = 0.5
                scale_factor_y = 0.5
                
                roi_x = max(0, x - int(w * scale_factor_x))
                roi_y = max(0, y - int(h * scale_factor_y))
                roi_width = min(frame.shape[1] - roi_x, int(w * (1 + 2 * scale_factor_x)))
                roi_height = min(frame.shape[0] - roi_y, int(h * (1 + 2 * scale_factor_y)))

                roi_y = max(0, roi_y)
                roi_height = min(frame.shape[0] - roi_y, roi_height)

                roi = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]

                roi = self.ensure_aspect_ratio(roi, target_ratio=(4, 3))
                label = test(
                    image=roi,
                    model_dir='./resources/anti_spoof_models',
                    device_id=0
                )

                if label == 1:
                    self.update_capture_button_color('green')
                    self.show_preview(roi)
                    
                else:
                    self.update_capture_button_color('red', reset=True)
                    messagebox.showwarning("Intente de nuevo!", "FOTO NO ADECUADA!")
            else:
                messagebox.showwarning("Sin rostros", "No se detectaron caras.")
                self.update_capture_button_color('red', reset=True)
        else:
            messagebox.showwarning("Error", "No se pudo capturar el fotograma.")
            self.update_capture_button_color('red', reset=True)

    def ensure_aspect_ratio(self, image, target_ratio=(4, 3)):
        current_height, current_width = image.shape[:2]
        target_width = int(current_height * target_ratio[1] / target_ratio[0])
        
        if current_width != target_width:
            new_image = cv2.resize(image, (target_width, current_height))
            return new_image
        return image

    def show_preview(self, rostro):
        self.preview_window = tk.Toplevel(self.window)
        self.preview_window.overrideredirect(True)
        self.preview_window.configure(bg='blue4')

        window_width = 260
        window_height = 320
        self.preview_window.geometry(f"{window_width}x{window_height}")

        x = self.window.winfo_x() + (self.window.winfo_width() - window_width) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - window_height) // 2

        self.preview_window.geometry(f"+{x}+{y}")
        self.preview_window.attributes('-topmost', True)

        resized_image = cv2.resize(rostro, (window_width, window_height - 48))

        image_pil = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(image=image_pil)

        label = tk.Label(self.preview_window, image=photo, bg='white')
        label.image = photo
        label.pack()

        btn_guardar = tk.Button(self.preview_window, text="Guardar", command=lambda: self.save_image(rostro), bg='green', fg='white', font=('Arial', 12))
        btn_guardar.pack(side=tk.LEFT, padx=10, pady=1)

        btn_volver = tk.Button(self.preview_window, text="Volver a Capturar", command=self.close_preview_window, bg='red', fg='white', font=('Arial', 12))
        btn_volver.pack(side=tk.RIGHT, padx=10, pady=1)

        btn_guardar.bind("<Enter>", lambda event, button=btn_guardar: button.config(bg='light green'))
        btn_guardar.bind("<Leave>", lambda event, button=btn_guardar: button.config(bg='green'))
        btn_volver.bind("<Enter>", lambda event, button=btn_volver: button.config(bg='pink'))
        btn_volver.bind("<Leave>", lambda event, button=btn_volver: button.config(bg='red'))

        btn_guardar.bind("<Button-1>", lambda event, button=btn_guardar: button.config(bg='dark green'))
        btn_guardar.bind("<ButtonRelease-1>", lambda event, button=btn_guardar: button.config(bg='light green'))
        btn_volver.bind("<Button-1>", lambda event, button=btn_volver: button.config(bg='dark red'))
        btn_volver.bind("<ButtonRelease-1>", lambda event, button=btn_volver: button.config(bg='red'))

    def preprocess_image(self, rostro):
        ycrcb_img = cv2.cvtColor(rostro, cv2.COLOR_BGR2YCrCb)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        ycrcb_img[:, :, 0] = clahe.apply(ycrcb_img[:, :, 0])
        processed_image = cv2.cvtColor(ycrcb_img, cv2.COLOR_YCrCb2BGR)
        return processed_image

    def save_image(self, rostro):
        etiqueta = self.entry_etiqueta.get().strip()

        if not etiqueta:
            messagebox.showwarning("Campo vacío", "El campo RFC no puede estar vacío.")
            self.update_capture_button_color('red')
            return

        if not self.validar_rfc(etiqueta):
            messagebox.showwarning("RFC inválido", "El RFC debe tener 13 caracteres alfanuméricos.")
            self.update_capture_button_color('red')
            return

        etiqueta = etiqueta.strip()

        ruta_imagen = f'{self.directoriorostros}/{etiqueta}.jpg'
        ruta_pickle = f'{self.directorio_pickle}/{etiqueta}.pickle'

        if os.path.exists(ruta_imagen):
            confirm = messagebox.askyesno("RFC duplicado", "Ya existe una imagen guardada con este RFC. ¿Desea actualizar la foto?")
            if not confirm:
                self.update_capture_button_color('red')
                return

        if not os.path.exists(self.directoriorostros):
            os.makedirs(self.directoriorostros)

        if not os.path.exists(self.directorio_pickle):
            os.makedirs(self.directorio_pickle)
            
        rostro = self.preprocess_image(rostro)

        cv2.imwrite(ruta_imagen, rostro)

        embeddings = face_recognition.face_encodings(rostro)
        if len(embeddings) > 0:
            with open(ruta_pickle, 'wb') as f:
                pickle.dump(embeddings[0], f)

            self.contador += 1
            messagebox.showinfo("Captura Exitosa", "Rostro guardado correctamente.")
        else:
            messagebox.showwarning("Error", "No se pudieron obtener embeddings del rostro.")

        self.close_preview_window()

    def close_preview_window(self):
        if hasattr(self, 'preview_window'):
            self.preview_window.destroy()
        self.reset_capture_button_color()

    def update_capture_button_color(self, color, reset=False, duration=1000):
        self.btn_capture.config(bg=color)
        if reset:
            self.window.after(duration, self.reset_capture_button_color)

    def reset_capture_button_color(self):
        self.btn_capture.config(bg=self.initial_btn_color)

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def stop_drag(self, event):
        self.x = None
        self.y = None

    def on_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
