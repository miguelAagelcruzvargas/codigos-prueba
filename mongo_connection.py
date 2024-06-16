# este si jalo hace rato 
from pymongo import MongoClient
from dateutil.parser import parse
from datetime import datetime
import pytz
import time
import os
import threading

def get_db():
    client = MongoClient("mongodb://localhost:27017/")  # Cambia esto según tu configuración
    #client = MongoClient("mongodb://192.168.1.125:5376/")
    db = client["sistemachecador"]  # Cambia el nombre de la base de datos
    print("esta es la base",db)
    return db


def convertir_a_formato_24hrs(horas):
    horas_24hrs = []
    for hora in horas:
        if isinstance(hora, datetime):
            hora = hora.strftime("%H:%M")
        try:
            horas_24hrs.append(hora)
        except ValueError as e:
            print(f"Error al convertir hora: {hora}. Detalles: {str(e)}")
    return horas_24hrs


from datetime import datetime, timedelta

def get_info(db, collection_name):
    collection = db[collection_name]
    current_date = datetime.now()

    # Buscar un documento donde la fecha actual esté entre Fecha de creacion y Fecha de vencimiento
    data = collection.find_one({
        'Fecha de creacion': {'$lte': current_date.isoformat()},
        'Fecha de vencimiento': {'$gte': current_date.isoformat()}
    })
    if data and 'Aviso' in data:
        return data['Aviso']
    else:
        return None

def get_admin_message_by_rfc(db, rfc):
    current_date = datetime.now()
    try:
        # Asegúrate de que tu colección y los nombres de los campos son correctos
        info = db.get_collection('Avisos').find_one({
            "RFC": rfc,
            "Fecha de creacion": {"$lte": current_date.isoformat()},
            "Fecha de vencimiento": {"$gte": current_date.isoformat()}
        })
        if info:
            return info.get('Aviso', "No hay mensaje del administrador.")
    except Exception as e:
        return f"Error al obtener el mensaje del administrador: {str(e)}"


def get_rfc_by_name(db, name):
    try:
        # Asegúrate de que el nombre del campo que contiene el nombre en tu colección es correcto
        info = db.get_collection('PRUEBA_HORARIO').find_one({"RFC": name})
        if info:
            return info.get('RFC', None)  # Asegúrate de que el campo 'RFC' está correctamente escrito
        else:
            return None
    except Exception as e:
        return f"Error al buscar el RFC: {str(e)}"


def update_entry_by_rfc(db, rfc):
    current_time = datetime.now()  # Hora actual para registrar la entrada
    fecha_actual_str = current_time.strftime("%Y-%m-%d") + "T00:00.000Z"  # Formato fecha día ISO

    try:
        result = db.get_collection('PRUEBA_HORARIO').update_one(
            {"RFC": rfc, "Fechas.fecha_dia": fecha_actual_str},
            {"$set": {
                "Fechas.$.HEC.0.hora_entrada": current_time,
                "Fechas.$.HEC.0.PRUEBA_HORARIO": "NORMAL"
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

def determine_check_type(db, rfc):
    current_time = datetime.now()
    fecha_actual_str = current_time.strftime("%Y-%m-%d") + "T00:00.000Z"
    documento = db.get_collection('PRUEBA_HORARIO').find_one(
        {"RFC": rfc, "tipo_horario": "abierto", "Fechas.fecha_dia": fecha_actual_str}
    )
    if documento:
        hec = documento["Fechas"][0].get("HEC", [])
        hsc = documento["Fechas"][0].get("HSC", [])
        if not hec or (len(hec) > len(hsc)):
            return "salida"
    return "entrada"




def add_open_schedule_check(db, rfc, check_type):
    from datetime import datetime

    current_time = datetime.now()
    fecha_actual_str = current_time.strftime("%Y-%m-%d") + "T00:00:00.000Z"
    end_of_day = current_time.replace(hour=23, minute=59, second=59)

    try:
        documento = db.get_collection('PRUEBA_HORARIO').find_one(
            {"RFC": rfc, "tipo_horario": "Abierto", "Fechas.fecha_dia": fecha_actual_str}
        )

        if documento:
            # Encontrar el subdocumento con la fecha actual en el array Fechas
            index = next((i for i, f in enumerate(documento["Fechas"]) if f["fecha_dia"] == fecha_actual_str), None)

            if index is not None:
                hec = documento["Fechas"][index].get("HEC", [])
                hsc = documento["Fechas"][index].get("HSC", [])

                hec_no_registradas = [i for i, e in enumerate(hec) if not e.get("registrado", False)]
                hsc_no_registradas = [i for i, s in enumerate(hsc) if not s.get("registrado", False)]

                # Verificar cuál fue el último campo actualizado
                last_entry = hec[-1] if hec else None
                last_exit = hsc[-1] if hsc else None

                if last_entry and (not last_exit or last_entry['horario_entrada_r'] > last_exit['horario_salida_r']):
                    # Registrar salida
                    if hsc_no_registradas:
                        hsc_index = hsc_no_registradas[0]
                        update_field = f"Fechas.{index}.HSC.{hsc_index}"
                        db.get_collection('PRUEBA_HORARIO').update_one(
                            {"RFC": rfc, "tipo_horario": "Abierto", f"Fechas.{index}.fecha_dia": fecha_actual_str},
                            {"$set": {f"{update_field}.horario_salida_r": current_time,
                                      f"{update_field}.estatus_checador": "NORMAL",
                                      f"{update_field}.registrado": True}}
                        )
                    else:
                        db.get_collection('PRUEBA_HORARIO').update_one(
                            {"RFC": rfc, "tipo_horario": "Abierto", f"Fechas.{index}.fecha_dia": fecha_actual_str},
                            {"$push": {f"Fechas.{index}.HSC": {"horario_salida_r": current_time, "estatus_checador": "NORMAL", "registrado": True}}}
                        )
                    message = f"Hasta luego {rfc}, salida registrada a tiempo."
                else:
                    # Registrar entrada
                    if hec_no_registradas:
                        hec_index = hec_no_registradas[0]
                        update_field = f"Fechas.{index}.HEC.{hec_index}"
                        db.get_collection('PRUEBA_HORARIO').update_one(
                            {"RFC": rfc, "tipo_horario": "Abierto", f"Fechas.{index}.fecha_dia": fecha_actual_str},
                            {"$set": {f"{update_field}.horario_entrada_r": current_time,
                                      f"{update_field}.estatus_checador": "NORMAL",
                                      f"{update_field}.registrado": True}}
                        )
                    else:
                        db.get_collection('PRUEBA_HORARIO').update_one(
                            {"RFC": rfc, "tipo_horario": "Abierto", f"Fechas.{index}.fecha_dia": fecha_actual_str},
                            {"$push": {f"Fechas.{index}.HEC": {"horario_entrada_r": current_time, "estatus_checador": "NORMAL", "registrado": True}}}
                        )
                    message = f"Bienvenido {rfc}, llegaste a tiempo. Asistencia tomada."

                # Registrar una salida automática al final del día si no se ha registrado
                if current_time >= end_of_day and len(hec) > len(hsc):
                    db.get_collection('PRUEBA_HORARIO').update_one(
                        {"RFC": rfc, "tipo_horario": "Abierto", f"Fechas.{index}.fecha_dia": fecha_actual_str},
                        {"$push": {f"Fechas.{index}.HSC": {"horario_salida_r": end_of_day, "estatus_checador": "FALTA", "registrado": True}}}
                    )

                return message
        else:
            # Si no existe el documento, inicializa los datos para la fecha actual
            initial_data = {
                "fecha_dia": fecha_actual_str,
                "HEC": [{"horario_entrada_r": current_time, "estatus_checador": "NORMAL", "registrado": True}],
                "HSC": []
            }
            db.get_collection('PRUEBA_HORARIO').update_one(
                {"RFC": rfc, "tipo_horario": "Abierto"},
                {"$push": {"Fechas": initial_data}}
            )
            return "Fecha agregada y entrada registrada con éxito."

    except Exception as e:
        return f"Error al agregar el chequeo: {str(e)}"











def determine_next_action(hec, hsc, current_time):
    if not hec or (hec and not hsc):
        # No hay entradas o no hay salidas después de la última entrada
        return "HEC", {"hora_entrada": current_time, "PRUEBA_HORARIO": "NORMAL"}
    else:
        # Hay una entrada, verificamos la última acción
        last_hec = hec[-1] if hec else None
        last_hsc = hsc[-1] if hsc else None
        if last_hec and (not last_hsc or last_hec["hora_entrada"] > last_hsc.get("hora_salida", datetime.min)):
            return "HSC", {"hora_salida": current_time, "PRUEBA_HORARIO": "NORMAL"}
        else:
            return "HEC", {"hora_entrada": current_time, "PRUEBA_HORARIO": "NORMAL"}


    
def get_employee_schedule_type(db, rfc):
    try:
        employee_data = db.get_collection('PRUEBA_HORARIO').find_one({"RFC": rfc})
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


def convertir_a_formato_24hrs(horas):
    horas_24hrs = []
    for hora in horas:
        if isinstance(hora, datetime):
            hora = hora.strftime("%H:%M")
        try:
            horas_24hrs.append(hora)
        except ValueError as e:
            print(f"Error al convertir hora: {hora}. Detalles: {str(e)}")
    return horas_24hrs

def verificar_y_actualizar_horario_fechas(db, rfc):
    tz = pytz.timezone('America/Mexico_City')
    current_time = datetime.now(tz)

    days_map = {
        'Monday': 'LUNES',
        'Tuesday': 'MARTES',
        'Wednesday': 'MIERCOLES',
        'Thursday': 'JUEVES',
        'Friday': 'VIERNES',
        'Saturday': 'SABADO',
        'Sunday': 'DOMINGO'
    }
    weekday = days_map[current_time.strftime("%A")]

    documento = db.get_collection('PRUEBA_HORARIO').find_one({"RFC": rfc, "tipo_horario": "Cerrado"})
    if not documento:
        #print("No se encontró el documento para el RFC especificado.")
        return "No se encontró el documento."

    estatus_activos = all(horario.get('estatus', '').lower() == 'activo' for horario in documento.get('Horarios', []))
    if not estatus_activos:
        
        #print(f"El estatus para {rfc} es inactivo.")
        return f"El estatus para {rfc} es inactivo."

    dia_horarios = documento['Horarios'][0]['DIA'][weekday]
    if not dia_horarios:
        #print("No se encontraron horarios para el día de hoy.")
        return "No se encontraron horarios para el día de hoy."

    try:
        horas_entrada = [hora if isinstance(hora, str) else hora.isoformat() for hora in dia_horarios.get('Hora_entrada', [])]
        horas_salida = [hora if isinstance(hora, str) else hora.isoformat() for hora in dia_horarios.get('Hora_salida', [])]
    except Exception as e:
        #print(f"Error al convertir horas: {str(e)}")
        return f"Error al convertir horas: {str(e)}"

    #print(f"Horas de entrada en formato ISO 8601: {horas_entrada}")
    #print(f"Horas de salida en formato ISO 8601: {horas_salida}")

    try:
        horas_entrada_dt = [datetime.fromisoformat(hora) for hora in horas_entrada]
        horas_salida_dt = [datetime.fromisoformat(hora) for hora in horas_salida]
    except Exception as e:
        #print(f"Error al convertir horas: {str(e)}")
        return f"Error al convertir horas: {str(e)}"

    horas_entrada_24hrs = convertir_a_formato_24hrs(horas_entrada_dt)
    horas_salida_24hrs = convertir_a_formato_24hrs(horas_salida_dt)

    #print(f"Hora de entrada (Formato 24 hrs): {horas_entrada_24hrs}")
    #print(f"Hora de salida (Formato 24 hrs): {horas_salida_24hrs}")

    current_time_str = current_time.strftime("%H:%M")
    current_time_dt = datetime.strptime(current_time_str, "%H:%M").replace(year=current_time.year, month=current_time.month, day=current_time.day)

    #print(f"Hora actual: {current_time_dt}")

    formatted_date = current_time.strftime("%Y-%m-%dT00:00.000Z")
    #print(f"Fecha actual formateada: {formatted_date}")

    fecha_index = next((i for i, f in enumerate(documento['Fechas']) if f['fecha_dia'] == formatted_date), None)
    #print(f"Índice de la fecha en el documento: {fecha_index}")

    if fecha_index is None:
        #print("No hay registros para actualizar hoy.")
        return "No hay registros para actualizar hoy."

    estatus = "FALTA"  # Inicialmente se marca como falta
    update_field = None
    target_index = None
    falta_tipo = None

    # Verificación de horas de entrada
    for idx, hora in enumerate(horas_entrada_dt):
        hora_dt = hora.replace(year=current_time.year, month=current_time.month, day=current_time.day)
        diff = (current_time_dt - hora_dt).total_seconds() / 60

        #print(f"Comparando hora de entrada programada ({hora_dt}) con la hora actual ({current_time_dt}), diferencia en minutos: {diff}")

        if -30 <= diff <= 10:
            if documento['Fechas'][fecha_index]['HEC'][idx].get('registrado', False):
                return "Entrada ya registrada.", None
            estatus = "NORMAL"
            update_field = 'HEC'
            target_index = idx
            print(f"Estatus Entrada: {estatus} para el índice {idx}")
            break
        elif 10 <= diff <= 20:
            if documento['Fechas'][fecha_index]['HEC'][idx].get('registrado', False):
                return "Entrada ya registrada.", None
            estatus = "RETARDO"
            update_field = 'HEC'
            target_index = idx
            print(f"Estatus Entrada: {estatus} para el índice {idx}")
            break
        elif 20 <= diff <= 30:
            if documento['Fechas'][fecha_index]['HEC'][idx].get('registrado', False):
                return "Entrada ya registrada.", None
            estatus = "NOTA MALA"
            update_field = 'HEC'
            target_index = idx
            print(f"Estatus Entrada: {estatus} para el índice {idx}")
            break
        elif diff > 30:
            estatus = "FALTA"
            update_field = 'HEC'
            target_index = idx
            print(f"Estatus Entrada: {estatus} para el índice {idx}")
            continue  # No es necesario; podríamos quitarlo

    print(f"Estatus de entrada después de verificar las horas: {estatus}")
    print(f"Campo de actualización para entrada después de la verificación: {update_field}")
    print(f"Índice de objetivo para entrada después de la verificación: {target_index}")

    # Verificación de horas de salida si sigue siendo "FALTA"
    if estatus == "FALTA" and falta_tipo is None:
        for idx, hora in enumerate(horas_salida_dt):
            hora_dt = hora.replace(year=current_time.year, month=current_time.month, day=current_time.day)
            diff = (current_time_dt - hora_dt).total_seconds() / 60

            #print(f"Comparando hora de salida programada ({hora_dt}) con la hora actual ({current_time_dt}), diferencia en minutos: {diff}")

            if -60 <= diff <= 0:
                if documento['Fechas'][fecha_index]['HSC'][idx].get('registrado', False):
                    return "Salida ya registrada.", None
                estatus = "FALTA"
                update_field = 'HSC'
                target_index = idx
                print(f"Estatus Salida: {estatus} para el índice {idx}")
                break
            elif 0 <= diff <= 30:
                if documento['Fechas'][fecha_index]['HSC'][idx].get('registrado', False):
                    return "Salida ya registrada.", None
                estatus = "NORMAL"
                update_field = 'HSC'
                target_index = idx
                print(f"Estatus Salida: {estatus} para el índice {idx}")
                break
            elif diff > 30:
                estatus = "FALTA"
                update_field = 'HSC'
                target_index = idx
                print(f"Estatus Salida: {estatus} para el índice {idx}")
                continue  # No es necesario; podríamos quitarlo

    print(f"Estatus de salida después de verificar las horas: {estatus}")
    print(f"Campo de actualización para salida después de la verificación: {update_field}")
    print(f"Índice de objetivo para salida después de la verificación: {target_index}")

    # Si no se encontró ningún estatus válido
    if falta_tipo:
        estatus = "FALTA"
        print(f"Resultado final: FALTA en {falta_tipo}")
        return f"FALTA en {falta_tipo}", None

    if estatus and update_field is not None:
        time_key = "horario_entrada_r" if update_field == 'HEC' else "horario_salida_r"
        action_type = "entrada" if update_field == 'HEC' else "salida"
        update_path = f"Fechas.{fecha_index}.{update_field}.{target_index}"

        update_data = {
            f"{update_path}.estatus_checador": estatus,
            f"{update_path}.{time_key}": current_time_dt.replace(tzinfo=None),
            f"{update_path}.registrado": True  # Marca el horario como registrado
        }

        result = db.get_collection('PRUEBA_HORARIO').update_one({"_id": documento['_id']}, {"$set": update_data})

        print(f"Datos de actualización: {update_data}")
        print(f"Resultado de la actualización: {result.modified_count}")

        return estatus, action_type
    else:
        print("No se pudo actualizar el estatus adecuadamente.")
        return "No se pudo actualizar el estatus adecuadamente."

###################################################################
db = get_db()
rfc = "HERM9209186WA"  # Ejemplo de RFC
check_type = determine_check_type(db, rfc)
resultado = add_open_schedule_check(db, rfc, check_type)
print(resultado)
