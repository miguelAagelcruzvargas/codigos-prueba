
from datetime import datetime, timedelta
from pymongo import MongoClient

def convertir_dia_a_espanol(dia_ingles):
    dias_espanol = {
        "MONDAY": "LUNES",
        "TUESDAY": "MARTES",
        "WEDNESDAY": "MIÉRCOLES",
        "THURSDAY": "JUEVES",
        "FRIDAY": "VIERNES",
        "SATURDAY": "SABADO",
        "SUNDAY": "DOMINGO"
    }
    return dias_espanol.get(dia_ingles, None)

def convertir_a_formato_24hrs(horas):
    horas_24hrs = []
    for hora in horas:
        if isinstance(hora, datetime):
            # Si la hora es un objeto datetime, convertirlo a cadena de texto
            hora = hora.strftime("%I:%M %p")
        try:
            hora_24hrs = datetime.strptime(hora, "%I:%M %p").strftime("%H:%M")
            horas_24hrs.append(hora_24hrs)
        except ValueError as e:
            print(f"Error al convertir hora: {hora}. Detalles: {str(e)}")
            
            
    return horas_24hrs
# Añadimos manejo de errores al determinar el tipo de hora actual
def determinar_tipo_hora_actual(hora_actual, horas_establecidas, tipo_hora):
    print(f"Tipo de hora: {tipo_hora}, Hora actual: {hora_actual}")
    tolerancia_retardo = timedelta(minutes=10) # Tolerancia para entrada después de la hora establecida
    margen_anticipacion_entrada = timedelta(minutes=30) # Margen de anticipación para entrada antes de la hora establecida
    estatus = None


    for hora_establecida in horas_establecidas:
        try:
            hora_establecida_dt = datetime.strptime(hora_establecida, "%H:%M")
        except ValueError as e:
            error_msg = f"Error al convertir la hora establecida: {hora_establecida}. Detalles: {str(e)}"
            print(error_msg)
            
            continue  # Saltamos a la siguiente iteración del bucle
        
        hora_establecida_limite_retardo = hora_establecida_dt + tolerancia_retardo
        hora_establecida_margen_entrada = hora_establecida_dt - margen_anticipacion_entrada

        try:
            hora_actual_dt = datetime.strptime(hora_actual, "%H:%M")
        except ValueError as e:
            error_msg = f"Error al obtener la hora actual. Detalles: {str(e)}"
            print(error_msg)
           
            continue  # Saltamos a la siguiente iteración del bucle

        if tipo_hora == "Entrada":
            if hora_actual_dt < hora_establecida_margen_entrada:
                print(f"Entrada fuera de rango (Demasiado temprano)")
                estatus = "FUERA DE RANGO"
            elif hora_actual_dt > hora_establecida_limite_retardo:
                print(f"Entrada fuera de rango (Demasiado tarde)")
                estatus = "FUERA DE RANGO"
            else:
                print(f"{tipo_hora} registrado (NORMAL)")
                estatus = "NORMAL"
                # Si se encontró una hora de entrada válida, salimos del bucle
                break
        elif tipo_hora == "Salida":
            if hora_actual_dt < hora_establecida_dt:
                print(f"{tipo_hora} fuera de rango")
                #estatus = "FUERA DE RANGO"
            elif hora_actual_dt > hora_establecida_dt:
                print(f"{tipo_hora} no registrado")
                estatus = "NO REGISTRADO"
            else:
                print(f"{tipo_hora} registrado (NORMAL)")
                estatus = "NORMAL"
                # Si se encontró una hora de salida válida, salimos del bucle
                break
    
    return estatus





# Manejo de errores para la conexión a la base de datos y la obtención del documento
try:
    client = MongoClient('mongodb://localhost:27017/',connectTimeoutMS=30000)
    db = client['sistemachecador']
    coleccion = db['catalogo_horario']

    # Obtener el día actual en español
    dia_actual = convertir_dia_a_espanol(datetime.now().strftime("%A").upper())

    # Buscar el documento por RFC
    documento = coleccion.find_one({'RFC': 'CAOW021027J8P'})
    
    if documento:
        # Acceder a la lista de horarios
        horarios = documento.get('Horarios', [])
        for horario in horarios:
            # Acceder a la información para el día actual
            info_dia_actual = horario.get('DIA', {}).get(dia_actual, None)
            if info_dia_actual:
                print(f"Día: {dia_actual}")
                # Acceder a la hora de entrada y salida para el día actual
                hora_entradas = info_dia_actual.get('Hora_entrada', [])
                hora_salidas = info_dia_actual.get('Hora_salida', [])
                
                
                hora_entradas_24hrs = convertir_a_formato_24hrs(hora_entradas)
                hora_salidas_24hrs = convertir_a_formato_24hrs(hora_salidas)
                print(f"Hora de entrada (Formato 24 hrs): {hora_entradas_24hrs}")
                print(f"Hora de salida (Formato 24 hrs): {hora_salidas_24hrs}")
                
                # Obtener la hora actual en formato 24 horas
                hora_actual_24hrs = datetime.now().strftime("%H:%M")
                
                # Determinar el tipo de hora actual para entrada y salida
                estatus_entrada = determinar_tipo_hora_actual(hora_actual_24hrs, hora_entradas_24hrs, "Entrada")
                estatus_salida = determinar_tipo_hora_actual(hora_actual_24hrs, hora_salidas_24hrs, "Salida")
                
                hora_actual = datetime.utcnow()
                
                fecha_actual = hora_actual.replace(hour=0, minute=0, second=0, microsecond=0)
             
                fecha_actual_str = fecha_actual.isoformat() + 'Z' 
                            
                # Buscar si ya existe un documento con la fecha actual dentro del array 'Fechas'
                documento_existente =  coleccion.find_one({"Fechas.fecha_dia": fecha_actual_str})

                if documento_existente:
                    # Obtener los campos HEC y HSC del documento existente
                    hec_actual = documento_existente.get("HEC", [])
                    hsc_actual = documento_existente.get("HSC", [])
                    
                    # Verificar si los campos HEC y HSC están llenos
                    if len(hec_actual) < 2:
                        # Agregar un nuevo subdocumento HEC si no está lleno
                        update_hec = {"$push": {
                            "Fechas.$.HEC": {
                                "hora_entrada": hora_actual,
                                "estatus_checador": estatus_entrada
                            }
                        }}
                        coleccion.update_one({"Fechas.fecha_dia": fecha_actual_str}, update_hec)
                    
                    if len(hsc_actual) < 2:
                        # Agregar un nuevo subdocumento HSC si no está lleno
                        update_hsc = {"$push": {
                            "Fechas.$.HSC": {
                                "hora_salida": hora_actual,
                                "estatus_checador": estatus_salida
                            }
                        }}
                        coleccion.update_one({"Fechas.fecha_dia": fecha_actual_str}, update_hsc)
                else:
                    # Crear un nuevo subdocumento dentro del array 'Fechas'
                    nuevo_subdocumento = {
                        "fecha_dia": fecha_actual_str,
                        "HEC": [{
                            "hora_entrada": hora_actual,
                            "estatus_checador": estatus_entrada
                        }],
                        "HSC": [{
                            "hora_salida": hora_actual,
                            "estatus_checador": estatus_salida
                        }]
                    }
                    # Agregar el nuevo subdocumento al array 'Fechas' si no hay un documento para la fecha actual
                    coleccion.update_one({}, {"$push": {"Fechas": nuevo_subdocumento}}, upsert=True)

            
        
            else:
                print(f"No se encontró información para el día actual ({dia_actual}).")
    else:
        print("Usted no tiene un horario asignado, acuda con el administrador.")
        
except Exception as e:
    if "not found" in str(e):
        print("Usted no tiene un horario asignado.")
    else:
        error_message = "Error al intentar conectar con la base de datos. Por favor, contacta al administrador del sistema para obtener ayuda."
        print(error_message)
        with open('error_log.txt', 'a') as log_file:
            log_file.write(f"Ocurrió un error: {str(e)}\n")

finally:
    # Cerrar la conexión a la base de datos al finalizar
    if 'client' in locals():
        client.close()
