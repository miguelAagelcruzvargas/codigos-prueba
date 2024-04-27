import pymongo
from datetime import datetime

# Conexión a la base de datos
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['sistemachecador']
collection = db['catalogo_horario']

# Obtener la hora actual
hora_actual = datetime.utcnow()
fecha_actual = hora_actual.replace(hour=0, minute=0, second=0, microsecond=0)

# Nuevo estatus para actualizar
nuevo_estatus_checador = "normalitp"

# Buscar si ya existe un documento con la fecha actual
documento_existente = collection.find_one({"Fechas.fecha_dia": fecha_actual})

if documento_existente:
    # Obtener los campos HEC y HSC del documento existente
    hec_actual = documento_existente.get("HEC", [])
    hsc_actual = documento_existente.get("HSC", [])
    
    # Verificar si los campos HEC y HSC están llenos
    if len(hec_actual) < 2:
        # Agregar un nuevo subdocumento HEC
        update_hec = {"$push": {
            "Fechas.$.HEC": {
                "hora_entrada": hora_actual,
                "estatus_checador": nuevo_estatus_checador
            }
        }}
        collection.update_one({"Fechas.fecha_dia": fecha_actual}, update_hec)
    
    if len(hsc_actual) < 2:
        # Agregar un nuevo subdocumento HSC
        update_hsc = {"$push": {
            "Fechas.$.HSC": {
                "hora_salida": hora_actual,
                "estatus_checador": nuevo_estatus_checador
            }
        }}
        collection.update_one({"Fechas.fecha_dia": fecha_actual}, update_hsc)
else:
    # Crear un nuevo subdocumento dentro del array Fechas
    nuevo_subdocumento = {
        "fecha_dia": fecha_actual,
        "HEC": [{
            "hora_entrada": hora_actual,
            "estatus_checador": nuevo_estatus_checador
        }],
        "HSC": [{
            "hora_salida": hora_actual,
            "estatus_checador": nuevo_estatus_checador
        }]
    }
    collection.update_one({}, {"$push": {"Fechas": nuevo_subdocumento}})
