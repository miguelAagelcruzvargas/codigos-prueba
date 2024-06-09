import cv2
import tkinter as tk
from PIL import Image, ImageTk
import dlib
import os
import pickle
import face_recognition

def recognize(img, db_path):
    embeddings_unknown = face_recognition.face_encodings(img)
    if len(embeddings_unknown) == 0:
        return 'no_persons_found'
    else:
        embeddings_unknown = embeddings_unknown[0]

    db_dir = sorted(os.listdir(db_path))

    match = False
    j = 0
    while not match and j < len(db_dir):
        path_ = os.path.join(db_path, db_dir[j])
        with open(path_, 'rb') as file:
            embeddings = pickle.load(file)

        match = face_recognition.compare_faces([embeddings], embeddings_unknown, tolerance=0.4)[0]
        j += 1

    if match:
        return db_dir[j - 1][:-7]
    else:
        return 'unknown_person'

class App:
    def __init__(self, window):
        self.window = window
        self.window.title("Detección de Rostros")
        self.window.geometry("800x600")
        
        self._label = tk.Label(window)
        self._label.pack()

        self.cap = cv2.VideoCapture(0)  # URL de la cámara IP
        self.detector = dlib.get_frontal_face_detector()
        self.tracker = dlib.correlation_tracker()
        self.tracking_face = False
        self.db_path = 'imagenes_pickle'
        
        self.update()

    def update(self):
        self.process_webcam()
        self.window.after(1, self.update)  # Actualizar cada 10ms para mejorar la fluidez

    def process_webcam(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            return

        frame = cv2.flip(frame, 1)  # Refleja el frame para simular un espejo
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.detector(gray_frame)
        if len(faces) > 0:
            largest_face = max(faces, key=lambda rect: rect.width() * rect.height())
            self.tracker.start_track(frame, largest_face)
            self.tracking_face = True

        if self.tracking_face:
            tracking_quality = self.tracker.update(frame)
            if tracking_quality >= 7:  # Umbral de calidad para el seguimiento
                tracked_position = self.tracker.get_position()
                x, y, w, h = (int(tracked_position.left()), int(tracked_position.top()), 
                              int(tracked_position.width()), int(tracked_position.height()))
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 1)

                # Verificar si el rostro ya está registrado
                roi_color = frame[y:y+h, x:x+w]
                rostro = cv2.resize(roi_color, (0, 0), fx=0.5, fy=0.5)
                result = recognize(rostro, self.db_path)
                
                if result != 'unknown_person' and result != 'no_persons_found':
                    cv2.putText(frame, f"Rostro registrado: {result}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                elif result == 'no_persons_found':
                    cv2.putText(frame, "No se detectaron rostros", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                self.tracking_face = False  # Detiene el seguimiento si la calidad es baja

        img_ = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(img_)
        imgtk = ImageTk.PhotoImage(image=pil_image)

        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)

        self.most_recent_capture_arr = frame

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
