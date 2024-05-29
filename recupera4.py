import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import os
import tkinter as tk
from tkinter import Label, Entry, Button, StringVar,messagebox
import json

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'mongo_host': 'localhost',
        'mongo_port': '27017',
        'mongo_user': '',
        'mongo_password': '',
        'fotos_path': 'C:\\Users\\isc20\\Downloads\\Silent-Face-Anti-Spoofing-master_INTERFAZ\\db',
        'huellas_path': 'C:\\Users\\isc20\\Downloads\\Silent-Face-Anti-Spoofing-master_INTERFAZ\\huellas'
    }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def create_gui(config):
    """
    Crea una ventana GUI para pedir la dirección IP, puerto, usuario y contraseña de MongoDB,
    y las rutas para guardar las fotos y huellas.
    """
    window = tk.Tk()
    window.title("MongoDB Configuration")
    window.geometry("400x400")  # Ajustado para acomodar más campos
    window.resizable(False, False)

    # Variables para almacenar la entrada del usuario
    host_var = StringVar(value=config['mongo_host'])
    port_var = StringVar(value=config['mongo_port'])
    user_var = StringVar(value=config['mongo_user'])
    password_var = StringVar(value=config['mongo_password'])
    fotos_path_var = StringVar(value=config['fotos_path'])
    huellas_path_var = StringVar(value=config['huellas_path'])

    # Etiquetas y entradas para el host, puerto, usuario, contraseña y rutas
    Label(window, text="MongoDB Host:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
    Entry(window, textvariable=host_var).grid(row=0, column=1, padx=10, pady=5)

    Label(window, text="MongoDB Port:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
    Entry(window, textvariable=port_var).grid(row=1, column=1, padx=10, pady=5)

    Label(window, text="MongoDB User (optional):").grid(row=2, column=0, padx=10, pady=5, sticky='e')
    Entry(window, textvariable=user_var).grid(row=2, column=1, padx=10, pady=5)

    Label(window, text="MongoDB Password (optional):").grid(row=3, column=0, padx=10, pady=5, sticky='e')
    Entry(window, textvariable=password_var, show="*").grid(row=3, column=1, padx=10, pady=5)

    Label(window, text="Fotos Save Path:").grid(row=4, column=0, padx=10, pady=5, sticky='e')
    Entry(window, textvariable=fotos_path_var).grid(row=4, column=1, padx=10, pady=5)

    Label(window, text="Huellas Save Path:").grid(row=5, column=0, padx=10, pady=5, sticky='e')
    Entry(window, textvariable=huellas_path_var).grid(row=5, column=1, padx=10, pady=5)

    results = []

    def validate_port(port):
        if port.isdigit() and 1 <= int(port) <= 65535:
            return True
        else:
            return False
    def on_submit():
        if not validate_port(port_var.get()):
            messagebox.showerror("Invalid Port", "Please enter a valid port number (1-65535).")
            return
        results.append({
            'mongo_host': host_var.get(),
            'mongo_port': port_var.get(),
            'mongo_user': user_var.get(),
            'mongo_password': password_var.get(),
            'fotos_path': fotos_path_var.get(),
            'huellas_path': huellas_path_var.get()
        })
        window.quit()

    Button(window, text="Submit", command=on_submit).grid(row=6, columnspan=2, pady=10)

    window.mainloop()
    if window.winfo_exists():
        window.destroy()
    return results[0] if results else config

def process_files(documents, directory, extension):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logging.info(f"Directorio {directory} creado.")
        except OSError as e:
            logging.error(f"Error al crear el directorio {directory}: {e}")
            return

    for doc in documents:
        filename = doc['filename']
        if filename.endswith(extension):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'wb') as file:
                    file.write(doc['file_data'])
                    logging.info(f"Archivo '{filename}' descargado y guardado en: {file_path}")
            except IOError as e:
                logging.error(f"Error de E/S al guardar el archivo {filename}: {e}")
            except Exception as e:
                logging.error(f"Error inesperado al guardar el archivo {filename}: {e}")

def main():
    config = load_config()
    config = create_gui(config)
    save_config(config)

    if not config['mongo_host'] or not config['mongo_port']:
        logging.error("No se proporcionaron detalles válidos de MongoDB. Terminando ejecución.")
        return

    # Construir la cadena de conexión condicionalmente
    if config['mongo_user'] and config['mongo_password']:
        mongo_connection_string = f"mongodb://{config['mongo_user']}:{config['mongo_password']}@{config['mongo_host']}:{config['mongo_port']}/"
    else:
        mongo_connection_string = f"mongodb://{config['mongo_host']}:{config['mongo_port']}/"
    
    try:
        client = MongoClient(mongo_connection_string, serverSelectionTimeoutMS=5000)
        db = client['sistemachecador']
        fotos_collection = db['fotos']
        huellas_collection = db['huellas']
    except Exception as e:
        logging.error(f"No se pudo establecer la conexión con MongoDB: {e}")
        return

    try:
        fotos_collection.create_index([("created_at", 1)])
        huellas_collection.create_index([("created_at", 1)])
    except Exception as e:
        logging.error(f"No se pudo crear el índice: {e}")

    last_checked = datetime.now() - timedelta(minutes=60)

    while True:
        try:
            fotos_query = {"created_at": {"$gt": last_checked}}
            foto_docs = list(fotos_collection.find(fotos_query))
            if foto_docs:
                logging.info(f"Se encontraron {len(foto_docs)} nuevos archivos .pickle. Iniciando descarga...")
                process_files(foto_docs, config['fotos_path'], '.pickle')

            huellas_query = {"created_at": {"$gt": last_checked}}
            huella_docs = list(huellas_collection.find(huellas_query))
            if huella_docs:
                logging.info(f"Se encontraron {len(huella_docs)} nuevos archivos .fpt. Iniciando descarga...")
                process_files(huella_docs, config['huellas_path'], '.fpt')

            if foto_docs or huella_docs:
                last_docs = foto_docs + huella_docs
                last_checked = max(doc['created_at'] for doc in last_docs)

            logging.info("Esperando nuevos archivos...")
            time.sleep(60)  # Esperar 60 segundos antes de la próxima comprobación

        except Exception as e:
            logging.error(f"Error al consultar o procesar documentos: {e}")
            logging.info("Reintentando en 60 segundos...")
            time.sleep(60)

if __name__ == "__main__":
    main()
