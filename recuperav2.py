import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import os

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        
        mongo_host = os.getenv('MONGO_HOST', '192.168.1.125')
        mongo_port = os.getenv('MONGO_PORT', '5376')
        mongo_connection_string = f"mongodb://{mongo_host}:{mongo_port}/"
        
        client = MongoClient(mongo_connection_string, serverSelectionTimeoutMS=5000)
        
        db = client['sistemachecador']
        fotos_collection = db['fotos']
        huellas_collection = db['huellas']
    except Exception as e:
        logging.error(f"No se pudo establecer la conexión con MongoDB: {e}")


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
    # Crear el directorio si aún no existe
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logging.info(f"Directorio {directory} creado.")
        except OSError as e:
            logging.error(f"Error al crear el directorio {directory}: {e}")
            return  # Si no podemos crear el directorio, no tiene sentido continuar

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


if __name__ == "__main__":
    main()
