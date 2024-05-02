from pymongo import MongoClient
from dateutil.parser import parse
import pytz
from datetime import datetime, timedelta
from pymongo import MongoClient

def get_db():
    try:
        client = MongoClient("mongodb://localhost:27017/")  # Cambia esto según tu configuración
        db = client["sistemachecador"]  # Cambia el nombre de la base de datos
        return db
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None



def get_info(db, collection_name):
    collection = db[collection_name]
    current_date = datetime.now()
    # Buscar un documento donde la fecha actual esté entre Fecha_inicial y Fecha_final
    data = collection.find_one({
        'Fecha_inicial': {'$lte': current_date},
        'Fecha_final': {'$gte': current_date}
    })
    if data and 'mensaje_administrador' in data:
        return data['mensaje_administrador']
    else:
        return None

def get_admin_message_by_rfc(db, rfc):
    current_date = datetime.now()
    try:
        # Asegúrate de que tu colección y los nombres de los campos son correctos
        info = db.get_collection('avisos_trabajador').find_one({
            "rfc": rfc,
            "Fecha_inicial": {"$lte": current_date},
            "Fecha_final": {"$gte": current_date}
        })
        if info:
            return info.get('mensaje_administrador', "No hay mensaje del administrador.")
    except Exception as e:
        return f"Error al obtener el mensaje del administrador: {str(e)}"

def get_rfc_by_name(db, name):
    try:
        # Asegúrate de que el nombre del campo que contiene el nombre en tu colección es correcto
        info = db.get_collection('catalogos_horario').find_one({"RFC": name})
        if info:
            return info.get('RFC', None)  # Asegúrate de que el campo 'RFC' está correctamente escrito
        else:
            return None
    except Exception as e:
        return f"Error al buscar el RFC: {str(e)}"

#----------------------------PARTE PARA LA ASISTENCIA-----------------------------------#

def update_entry_by_rfc(db, rfc):
    current_time = datetime.now()  # Hora actual para registrar la entrada
    fecha_actual_str = current_time.strftime("%Y-%m-%d") + "T00:00:00.000Z"  # Formato fecha día ISO

    try:
        result = db.get_collection('catalogos_horario').update_one(
            {"RFC": rfc, "Fechas.fecha_dia": fecha_actual_str},
            {"$set": {
                "Fechas.$.HEC.0.hora_entrada": current_time,
                "Fechas.$.HEC.0.estatus_checador": "NORMAL"
            }}
        )
        if result.modified_count > 0:
            return "Actualización exitosa."
        else:
            return "No se encontraron registros para actualizar o fecha no coincide."
    except Exception as e:
        return f"Error al actualizar la entrada: {str(e)}"

def get_employee_schedule_type_and_entry(db, rfc):
    # Esta función necesita ser definida para obtener el tipo de horario y determinar si la próxima acción es una entrada o salida.
    return "abierto", "entrada"

def add_open_schedule_check(db, rfc, check_type):
    current_time = datetime.now()
    fecha_actual_str = current_time.strftime("%Y-%m-%d") + "T00:00:00.000Z"  # Formato de fecha día ISO
    end_of_day = current_time.replace(hour=23, minute=59, second=59)  # Establecer el momento de cierre del día
    end_of_day_str = end_of_day.strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # Convertir a string

    try:
        documento = db.get_collection('catalogo_horario').find_one(
            {"RFC": rfc, "tipo_horario": "abierto", "Fechas.fecha_dia": fecha_actual_str}
        )

        if documento:
            hec = documento["Fechas"][0].get("HEC", [])
            hsc = documento["Fechas"][0].get("HSC", [])
            current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # Convertir la hora actual a string

            if not hec:  # No hay entradas aún
                update_field = "HEC"
                update_data = {"hora_entrada": current_time_str, "estatus_checador": "NORMAL"}
            elif len(hec) > len(hsc):  # Hay más entradas que salidas, registra una salida
                update_field = "HSC"
                update_data = {"hora_salida": current_time_str, "estatus_checador": "NORMAL"}
            else:  # El número de entradas y salidas es igual, registra una entrada
                update_field = "HEC"
                update_data = {"hora_entrada": current_time_str, "estatus_checador": "NORMAL"}

            # Actualizar el documento con la nueva entrada o salida
            result = db.get_collection('catalogo_horario').update_one(
                {"RFC": rfc, "tipo_horario": "abierto", "Fechas.fecha_dia": fecha_actual_str},
                {"$push": {f"Fechas.$.{update_field}": update_data}}
            )

            # Verificar al final del día si hay desbalance de entrada
            if current_time >= end_of_day and len(hec) > len(hsc):
                # Agregar salida faltante con estatus "FALTA"
                db.get_collection('catalogos_horario').update_one(
                    {"RFC": rfc, "tipo_horario": "abierto", "Fechas.fecha_dia": fecha_actual_str},
                    {"$push": {"Fechas.$.HSC": {"hora_salida": end_of_day_str, "estatus_checador": "FALTA"}}}
                )

            return "Chequeo agregado correctamente." if result.modified_count > 0 else "No se encontró el documento."
        else:
            # Si no hay documento para ese día, se crea uno nuevo con una entrada
            db.get_collection('catalogos_horario').insert_one(
                {"RFC": rfc, "tipo_horario": "abierto", "Fechas": [{"fecha_dia": fecha_actual_str, "HEC": [{"hora_entrada": current_time_str, "estatus_checador": "NORMAL"}], "HSC": []}]}
            )
            return "Documento creado y chequeo registrado."
    except Exception as e:
        return f"Error al agregar el chequeo: {str(e)}"


def determine_next_action(hec, hsc, current_time):
    if not hec or (hec and not hsc):
        # No hay entradas o no hay salidas después de la última entrada
        return "HEC", {"hora_entrada": current_time, "estatus_checador": "NORMAL"}
    else:
        # Hay una entrada, verificamos la última acción
        last_hec = hec[-1] if hec else None
        last_hsc = hsc[-1] if hsc else None
        if last_hec and (not last_hsc or last_hec["hora_entrada"] > last_hsc.get("hora_salida", datetime.min)):
            return "HSC", {"hora_salida": current_time, "estatus_checador": "NORMAL"}
        else:
            return "HEC", {"hora_entrada": current_time, "estatus_checador": "NORMAL"}

    
def get_employee_schedule_type(db, rfc):
    try:
        employee_data = db.get_collection('catalogo_horario').find_one({"RFC": rfc})
        if employee_data:
            return employee_data.get('tipo_horario', None)
        else:
            return None
    except Exception as e:
        print(f"Error al obtener el tipo de horario: {str(e)}")
        return None


def obtener_nombre_dia():
    dias_espanol = {
        0: "LUNES",
        1: "MARTES",
        2: "MIERCOLES",
        3: "JUEVES",
        4: "VIERNES",
        5: "SABADO",
        6: "DOMINGO"
    }
    dia_actual = datetime.now().weekday()
    return dias_espanol[dia_actual]

def verificar_horario_cerrado(db, rfc):
    dia_actual = obtener_nombre_dia()
    hora_actual = datetime.now()

    # Consulta para verificar el RFC y el tipo de horario
    documento = db.get_collection('catalogo_horario').find_one({
        "RFC": rfc,
        "tipo_horario": "Cerrado",
        "Horarios.DIA.{}".format(dia_actual): {"$exists": True}
    })

    if documento:
        # Accediendo a las horas de entrada y salida programadas para el día actual
        horarios_dia = documento["Horarios"]["DIA"][dia_actual]
        horas_entrada = horarios_dia.get("Hora_entrada", [])
        horas_salida = horarios_dia.get("Hora_salida", [])

        # Verificar si la hora actual coincide con alguna hora de entrada o salida
        entrada_valida = any(hora_actual.time() == datetime.strptime(hora, "%Y-%m-%dT%H:%M:%S.%fZ").time() for hora in horas_entrada)
        salida_valida = any(hora_actual.time() == datetime.strptime(hora, "%Y-%m-%dT%H:%M:%S.%fZ").time() for hora in horas_salida)

        if entrada_valida or salida_valida:
            return "Hora de entrada o salida coincidente"
        else:
            return "No hay coincidencias de horario para ahora"
    else:
        return "No se encontró documento o no es horario cerrado para este día"

from datetime import datetime, timedelta

def verificar_y_actualizar_horario_fechas(db, rfc):
    tz = pytz.timezone('America/Mexico_City')
    current_time = datetime.now(tz)
    current_date_str = current_time.strftime("%Y-%m-%d") + "T00:00:00.000Z"

    days_map = {
        'Monday': 'LUNES',
        'Tuesday': 'MARTES',
        'Wednesday': 'MIERCOLES',
        'Thursday': 'JUEVES',
        'Friday': 'VIERNES',
        'Saturday': 'SABADO',
        'Sunday': 'DOMINGO'
    }
    ##################### fragmento para manejar horarios cerrados #################
    weekday = days_map[current_time.strftime("%A")]

    documento = db.get_collection('catalogo_horario').find_one({"RFC": rfc, "tipo_horario": "Cerrado"})
    if not documento:
        return "No se encontró el documento."

    dia_horarios = next((dia for dia in documento.get('Horarios', []) if dia.get('DIA', {}).get(weekday)), None)
    if not dia_horarios:
        return "No se encontraron horarios para el día de hoy."

    horas_entrada = [parse(hora).astimezone(tz) for hora in dia_horarios['DIA'][weekday].get('Hora_entrada', [])]
    horas_salida = [parse(hora).astimezone(tz) for hora in dia_horarios['DIA'][weekday].get('Hora_salida', [])]

    fecha_index = next((i for i, f in enumerate(documento['Fechas']) if f['fecha_dia'] == current_date_str), None)
    if fecha_index is None:
        return "No hay registros para actualizar hoy."

    min_diff = float('inf')
    estatus = None
    update_field = None
    target_index = None

    for idx, hora in enumerate(horas_entrada):
        diff = (current_time - hora).total_seconds() / 60
        if diff < min_diff:
            min_diff = diff
            update_field = 'HEC'
            target_index = idx
            if -30 <= diff <= 0:
                estatus = "NORMAL"
            elif 1 <= diff <= 10:
                estatus = "RETARDO"
            else:
                estatus = "FALTA"

    for idx, hora in enumerate(horas_salida):
        diff = (current_time - hora).total_seconds() / 60
        if diff < min_diff:
            min_diff = diff
            update_field = 'HSC'
            target_index = idx
            if diff < 0:
                continue  # No update if before scheduled time
            elif 0 <= diff <= 30:
                estatus = "NORMAL"
            else:
                estatus = "FALTA"

    if estatus and update_field is not None:
        time_key = "hora_entrada" if update_field == 'HEC' else "hora_salida"
        update_path = f"Fechas.{fecha_index}.{update_field}.{target_index}"
        update_data = {
            f"{update_path}.estatus_checador": estatus,
            f"{update_path}.{time_key}": current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }

        db.get_collection('catalogo_horario').update_one({"_id": documento['_id']}, {"$set": update_data})

        return "Chequeo actualizado correctamente."
    else:
        return "No se pudo actualizar el estatus adecuadamente."


def actualizar_horario(db, rfc, tipo, hora_real, estatus):
    fecha_actual_str = hora_real.strftime("%Y-%m-%dT00:00:00.000Z")
    update_data = {"hora_entrada" if tipo == "HEC" else "hora_salida": hora_real, "estatus_checador": estatus}
    
    result = db.get_collection('catalogo_horario').update_one(
        {"RFC": rfc, "Fechas.fecha_dia": fecha_actual_str},
        {"$push": {f"Fechas.$.{tipo}": update_data}}
    )
    return "Actualizado" if result.modified_count > 0 else "No actualizado"
