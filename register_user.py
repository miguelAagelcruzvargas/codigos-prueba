import tkinter as tk
import os.path
import cv2
from PIL import Image, ImageTk
import face_recognition
import pickle
import util




class RegisterUserApp:
    def __init__(self):
        self.register_window = tk.Tk()
        self.register_window.geometry("1200x520+370+120")

        self.capture_label = util.get_img_label(self.register_window)
        self.capture_label.place(x=10, y=0, width=700, height=500)

        self.add_webcam(self.capture_label)

        self.entry_text_register_user = util.get_entry_text(self.register_window)
        self.entry_text_register_user.place(x=750, y=150)

        self.text_label_register_user = util.get_text_label(self.register_window, 'RFC (ID):')
        self.text_label_register_user.place(x=750, y=70)

        self.accept_button_register_user_window = util.get_button(self.register_window, 'Capturar', 'green',
                                                                   self.accept_register_user)
        self.accept_button_register_user_window.place(x=750, y=300)

        self.try_again_button_register_user_window = util.get_button(self.register_window, 'Try again', 'red',
                                                                      self.try_again_register_user)
        self.try_again_button_register_user_window.place(x=750, y=400)

        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)
            
    def validar_rfc(self, rfc):
        """
        Función para validar un RFC (Registro Federal de Contribuyentes) en México.
        Retorna True si el RFC es válido, False si no lo es.
        """
        # Longitud válida de un RFC
        if len(rfc) != 13:
            return False
        
        # Patrón de caracteres permitidos en un RFC
        caracteres_validos = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        
        # Validación de los primeros 4 caracteres (Letras)
        for char in rfc[:4]:
            if char.upper() not in caracteres_validos:
                return False
        
        # Validación del dígito numérico (Año de nacimiento)
        if not rfc[4:6].isdigit():
            return False
        
        # Validación del mes de nacimiento
        if not rfc[6:8].isdigit():
            return False
        
        # Validación del día de nacimiento
        if not rfc[8:10].isdigit():
            return False
        
        # Validación del dígito verificador (homoclave)
        if not rfc[10:].isalnum():
            return False
        
        return True

    def add_webcam(self, label):
        self.cap = cv2.VideoCapture(0)
        self._label = label
        self.process_webcam()

    def process_webcam(self):
        ret, frame = self.cap.read()
        frame = cv2.flip(frame, 1)

        self.most_recent_capture_arr = frame
        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)

        self._label.after(20, self.process_webcam)

    def accept_register_user(self):
        name = self.entry_text_register_user.get(1.0, "end-1c")
        
        # Validar la longitud del RFC
        if len(name) != 13:
            util.msg_box('Error', 'El RFC debe tener 13 caracteres.')
            return

        # Validar el RFC
        if not self.validar_rfc(name):
            util.msg_box('Error', 'El RFC ingresado no es válido.')
            return

        embeddings = face_recognition.face_encodings(self.most_recent_capture_arr)[0]

        # Guardar la imagen serializada en la carpeta local
        file_path = os.path.join(self.db_dir, '{}.pickle'.format(name))
        with open(file_path, 'wb') as file:
            pickle.dump(embeddings, file)
        


        util.msg_box('Exito!', 'Usuario capturado exitosamente!')

        self.register_window.destroy()

    def try_again_register_user(self):
        self.register_window.destroy()


if __name__ == "__main__":
    app = RegisterUserApp()
    app.register_window.mainloop()
