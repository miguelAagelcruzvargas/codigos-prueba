import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import os

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    client = MongoClient("mongodb://192.168.1.125:5376/", serverSelectionTimeoutMS=5000)
    db = client['sistemachecador']
    fotos_collection = db['fotos']
    huellas_collection = db['huellas']

    try:
        fotos_collection.create_index([("created_at", 1)])
        huellas_collection.create_index([("created_at", 1)])
    except Exception as e:
        logging.error(f"No se pudo crear el índice: {e}")

    last_checked = datetime.now() - timedelta(minutes=60)

    while True:
        current_time = datetime.now()
        try:
            # Procesar fotos
            fotos_query = {"created_at": {"$gt": last_checked}}
            foto_docs = list(fotos_collection.find(fotos_query))
            if foto_docs:
                logging.info(f"Se encontraron {len(foto_docs)} nuevos archivos .pickle. Iniciando descarga...")
                process_files(foto_docs, 'C:\\Users\\isc20\\Downloads\\Silent-Face-Anti-Spoofing-master_INTERFAZ\\db', '.pickle')

            # Procesar huellas
            huellas_query = {"created_at": {"$gt": last_checked}}
            huella_docs = list(huellas_collection.find(huellas_query))
            if huella_docs:
                logging.info(f"Se encontraron {len(huella_docs)} nuevos archivos .fpt. Iniciando descarga...")
                process_files(huella_docs, 'C:\\Users\\isc20\\source\\repos\\codigos-para-lector-de-huella\\DemoDP4500\\bin\\Debug\\registros', '.fpt')

            # Actualizar last_checked
            if foto_docs or huella_docs:
                last_docs = foto_docs + huella_docs
                last_checked = max(doc['created_at'] for doc in last_docs)

            logging.info("Esperando nuevos archivos...")
            time.sleep(60)  # Esperar 60 segundos antes de la próxima comprobación

        except Exception as e:
            logging.error(f"Error al consultar o procesar documentos: {e}")
            logging.info("Reintentando en 60 segundos...")
            time.sleep(60)

def process_files(documents, directory, extension):
    for doc in documents:
        filename = doc['filename']
        if filename.endswith(extension):
            file_path = os.path.join(directory, filename)
            if not os.path.exists(directory):
                os.makedirs(directory)
            try:
                with open(file_path, 'wb') as file:
                    file.write(doc['file_data'])
                logging.info(f"Archivo '{filename}' descargado y guardado en: {file_path}")
            except Exception as e:
                logging.error(f"Error al guardar el archivo {filename}: {e}")

if __name__ == "__main__":
    main()
