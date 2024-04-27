import pymongo
from datetime import datetime

# Conexión a la base de datos
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['sistemachecador']
collection = db['catalogo_horario']

# Obtener la hora actual
hora_actual = datetime.utcnow()

# Nuevo estatus para actualizar
nuevo_estatus_checador = "NORMAL"

# Filtro para encontrar el documento específico
filtro = {"Fechas.fecha_dia": datetime(2024, 5, 10)}

# Verificar si los campos HEC están vacíos o nulos y actualizar si es necesario
hec_vacio = collection.find_one({"Fechas.fecha_dia": filtro["Fechas.fecha_dia"], "Fechas.HEC": {"$exists": False}})
if hec_vacio:
    # Actualizar HEC si está vacío
    update_hec = {"$set": {
        "Fechas.$.HEC": [{
            "hora_entrada": hora_actual,
            "estatus_checador": nuevo_estatus_checador
        }]
    }}
    collection.update_one(filtro, update_hec)

# Verificar si los campos HSC están vacíos o nulos y actualizar si es necesario
hsc_vacio = collection.find_one({"Fechas.fecha_dia": filtro["Fechas.fecha_dia"], "Fechas.HSC": {"$exists": False}})
if hsc_vacio:
    # Actualizar HSC si está vacío
    update_hsc = {"$set": {
        "Fechas.$.HSC": [{
            "hora_salida": hora_actual,
            "estatus_checador": nuevo_estatus_checador
        }]
    }}
    collection.update_one(filtro, update_hsc)

# Insertar nuevos subdocumentos HEC si no se actualizaron
if not hec_vacio:
    # Insertar nuevo subdocumento HEC
    update_hec_insert = {"$addToSet": {
        "Fechas.$.HEC": {
            "hora_entrada": hora_actual,
            "estatus_checador": nuevo_estatus_checador
        }
    }}
    collection.update_one(filtro, update_hec_insert)

# Insertar nuevos subdocumentos HSC si no se actualizaron
if not hsc_vacio:
    # Insertar nuevo subdocumento HSC
    update_hsc_insert = {"$addToSet": {
        "Fechas.$.HSC": {
            "hora_salida": hora_actual,
            "estatus_checador": nuevo_estatus_checador
        }
    }}
    collection.update_one(filtro, update_hsc_insert)
