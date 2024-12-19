import yaml
import os
import random
import getpass
from colorama import init, Fore, Style
from tabulate import tabulate
import re
from copy import deepcopy

# Inicializa colorama para dar estilo al texto en la CLI
init(autoreset=True)

# Definir como una variable global
db = None
notas_alumno_original = None

# Definición global de usuario
usuario = None

#ALUMNOS **********************************************************************************************************************************************

# Función para cargar la base de datos YAML
def cargar_base_datos():
    ruta = os.path.join(os.path.dirname(__file__), "database.yaml")
    with open(ruta, 'r', encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)

# Función para mostrar el banner principal
def mostrar_banner():
    print(Fore.CYAN + Style.BRIGHT + "\n=====================================")
    print("     Sistema de Gestión PUCP")
    print("=====================================\n" + Style.RESET_ALL)

# Función para validar el formato del correo PUCP
def extraer_codigo(correo):
    patron = r"^a(\d{8})@pucp\.edu\.pe$"  # Regex: a + 8 dígitos + @pucp.edu.pe
    match = re.match(patron, correo)
    if match:
        return match.group(1)  # Devuelve solo el código (8 dígitos)
    return None

# Función para realizar el login
def login(usuarios):
    global usuario
    while True:
        print(Fore.YELLOW + ">> Inicio de sesión <<\n")
        correo = input("Ingrese su correo PUCP (@pucp.edu.pe): ").strip()
        contrasenia = getpass.getpass("Ingrese su contraseña: ").strip()

        # Extraer el código del correo
        codigo = extraer_codigo(correo)
        if not codigo:
            print(Fore.RED + "\nFormato de correo incorrecto. Intente nuevamente.\n")
            continue

        # Buscar si el usuario con ese código existe y validar la contraseña
        for u in usuarios:
            if u['codigo'] == int(codigo) and u['contrasenia'] == contrasenia:
                print(Fore.GREEN + "\n¡Inicio de sesión exitoso!\n")
                usuario = u  # Actualiza la variable global usuario
                return usuario  # Retorna el usuario logueado

        # Si no se encontró el usuario o la contraseña no coincide
        print(Fore.RED + "\nCredenciales incorrectas. Intente nuevamente.\n")

# Función para mostrar los cursos en los que está inscrito el estudiante
def ver_cursos(usuario, cursos, db):
    print(Fore.CYAN + Style.BRIGHT + "\n== Cursos Existentes ==\n")
    
    # Mostrar todos los cursos disponibles
    encabezados = ['Número', 'Código del Curso', 'Nombre del Curso']
    lista_cursos = [[index, curso['codigo_curso'], curso['nombre']] for index, curso in enumerate(cursos, start=1)]

    # Imprimir la tabla
    print(Fore.GREEN + tabulate(lista_cursos, headers=encabezados, tablefmt='grid'))

    print("\n0. Volver atrás")

    opcion = input(Fore.YELLOW + "Seleccione el curso por su número o '0' para volver: ").strip()

    if opcion == '0':
        return

    if opcion.isdigit() and 0 < int(opcion) <= len(cursos_inscritos):
        curso_seleccionado = cursos_inscritos[int(opcion)-1]
        mostrar_info_curso(curso_seleccionado, db)
    else:
        print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")
        ver_cursos(usuario, cursos, db)

# Función para mostrar más información de un curso
def mostrar_info_curso(curso, db):
    while True:
        print(Fore.CYAN + f"\n== {curso['nombre']} ==\n")
        print("1. Ver notas")
        print("2. Ver participantes")
        print("3. Volver atrás")

        opcion = input(Fore.YELLOW + "Seleccione una opción: ").strip()

        if opcion == '1':
            ver_notas(curso, db)
        elif opcion == '2':
            ver_participantes(curso)
        elif opcion == '3':
            return
        else:
            print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")

# Función para ver las notas de un curso
def ver_notas(curso, db):
    print(Fore.CYAN + f"== Notas del curso: {curso['nombre']} ==\n")
    
    # Crear una lista para almacenar las filas de la tabla
    notas_tabla = []

    # Iterar sobre las notas de todos los cursos
    for nota in db.get('notas', []):
        if nota['curso'] == curso['codigo_curso']:  # Si el curso coincide
            # Buscar las notas del alumno que corresponde al código del usuario
            for alumno in nota['alumnos']:
                if alumno['alumno'] == usuario['codigo']:  # Verificar si el código coincide
                    # Crear una fila para las notas
                    fila = [usuario['nombre']]  # Nombre del alumno
                    # Añadir las calificaciones a la fila
                    for materia, calificacion in alumno.items():
                        if materia != 'alumno':  # No mostrar el código del alumno
                            fila.append(calificacion)
                    notas_tabla.append(fila)
                    break

    # Generar las cabeceras dinámicamente, basadas en las claves de las notas
    if notas_tabla:
        # Obtener las claves de las primeras notas del alumno (excluyendo 'alumno')
        primera_fila = notas_tabla[0]
        cabeceras = ['Alumno'] + [key.capitalize() for key in alumno.keys() if key != 'alumno']
        
        # Imprimir la tabla
        print(Fore.GREEN + tabulate(notas_tabla, headers=cabeceras, tablefmt='grid'))
    else:
        print(Fore.RED + "No se encontraron notas para este alumno en este curso.")
    
    input(Fore.YELLOW + "\nPresione ENTER para volver atrás...")

# Función para ver los participantes de un curso
def ver_participantes(curso):
    print(Fore.CYAN + f"\n== Participantes del curso: {curso['nombre']} ==\n")
    
    # Obtener el profesor del curso
    profesor = next(usuario for usuario in db.get('usuarios', []) if usuario['codigo'] == curso['profesor'])
    profesor_nombre = profesor['nombre']
    
    # Obtener los alumnos del curso
    alumnos = []
    for alumno_codigo in curso['alumnos']:
        alumno = next(usuario for usuario in db.get('usuarios', []) if usuario['codigo'] == alumno_codigo)
        alumnos.append(alumno['nombre'])

    # Crear tabla con profesor y alumnos
    encabezados = ['Rol', 'Nombre']
    participantes = [['Profesor', profesor_nombre]] + [['Alumno', alumno] for alumno in alumnos]

    # Imprimir tabla
    print(Fore.GREEN + tabulate(participantes, headers=encabezados, tablefmt='grid'))

    input(Fore.YELLOW + "\nPresione ENTER para volver atrás...")

#*********************************************************************************************************************************************************

# Función para mostrar el menú dependiendo del rol y manejar las opciones
def mostrar_menu(usuario, db):
    while True:  # Bucle para mantener el menú activo hasta que se salga
        rol = usuario["rol"]
        print(Fore.BLUE + f"Bienvenido, {usuario['nombre']} ({rol})\n")
        print(Style.BRIGHT + "Seleccione una opción del menú:\n")

        # Opciones según el rol
        if rol == "Estudiante":
            print(Fore.MAGENTA + "1. Ver cursos existentes")
            print("2. Cerrar Sesión")
            opcion = input(Fore.YELLOW + "\nSeleccione una opción: ").strip()
            if opcion == '1':
                ver_cursos(usuario, db.get('cursos', []), db)
            elif opcion == '2':
                print("Cerrando sesión...")
                return
            else:
                print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")
        
        elif rol == "Profesor":
            print(Fore.GREEN + "1. Gestionar cursos")
            print("2. Salir")
            opcion = input(Fore.YELLOW + "\nSeleccione una opción: ").strip()
            if opcion == '1':
                gestionar_cursos_profesor(db.get('cursos', []))  # Función de ejemplo para gestionar cursos
            elif opcion == '2':
                print("Saliendo...")
                return
            else:
                print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")

        elif rol == "Administrador":
            print(Fore.RED + "1. Administrar usuarios")
            print("2. Administrar cursos")
            print("3. Cerrar sesión")
            opcion = input(Fore.YELLOW + "\nSeleccione una opción: ").strip()
            if opcion == '1':
                administrar_usuarios()  # Función para administrar usuarios
            elif opcion == '2':
                administrar_cursos()  # Función para administrar cursos
            elif opcion == '3':
                print("Cerrando sesión...")
                return
            else:
                print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")
        
        else:
            print(Fore.RED + "Error: Rol no reconocido.")
            return


#PROFESOR **********************************************************************************************************************************************
def gestionar_cursos_profesor(cursos):
    # Listar los cursos donde el profesor está asignado
    cursos_profesor = [curso for curso in cursos if curso['profesor'] == usuario['codigo']]
    
    if not cursos_profesor:
        print(Fore.RED + "No estás asignado a ningún curso.\n")
        return

    encabezados = ['Número', 'Código del Curso', 'Nombre del Curso']
    lista_cursos = [[index, curso['codigo_curso'], curso['nombre']] for index, curso in enumerate(cursos_profesor, start=1)]
    
    # Imprimir los cursos
    print(Fore.GREEN + tabulate(lista_cursos, headers=encabezados, tablefmt='grid'))
    
    print("\n0. Volver atrás")
    opcion = input(Fore.YELLOW + "Seleccione el curso por su número o '0' para volver: ").strip()

    if opcion == '0':
        return

    if opcion.isdigit() and 0 < int(opcion) <= len(cursos_profesor):
        curso_seleccionado = cursos_profesor[int(opcion) - 1]
        menu_curso_profesor(curso_seleccionado)
    else:
        print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")
        gestionar_cursos_profesor(cursos)

def menu_curso_profesor(curso):
    # Menú para el curso seleccionado
    while True:
        print(Fore.CYAN + f"\n== Curso: {curso['nombre']} ==\n")
        print("1. Ver notas de alumnos")
        print("2. Volver atrás")
        
        opcion = input(Fore.YELLOW + "Seleccione una opción: ").strip()

        if opcion == '1':
            ver_notas_profesor(curso)
        elif opcion == '2':
            return
        else:
            print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")

def ver_notas_profesor(curso):
    # Mostrar las notas de los alumnos del curso
    notas_curso = [nota for nota in db.get('notas', []) if nota['curso'] == curso['codigo_curso']]
    
    if not notas_curso:
        print(Fore.RED + "No hay notas disponibles para este curso.\n")
        return

    print(Fore.CYAN + "== Alumnos Inscritos ==\n")
    estudiantes = []

    # Extraer alumnos inscritos en el curso
    for nota in notas_curso:
        estudiantes.extend(nota['alumnos'])

    estudiantes = list({v['alumno']: v for v in estudiantes}.values())  # Eliminar duplicados

    # Imprimir lista de estudiantes
    for index, estudiante in enumerate(estudiantes, 1):
        print(f"{index}. {estudiante['alumno']}")

    print("\n0. Volver atrás")
    opcion = input(Fore.YELLOW + "Seleccione un estudiante para editar las notas o '0' para volver: ").strip()

    if opcion == '0':
        return

    if opcion.isdigit() and 0 < int(opcion) <= len(estudiantes):
        estudiante_seleccionado = estudiantes[int(opcion) - 1]
        menu_editar_notas(estudiante_seleccionado, curso)
    else:
        print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")
        ver_notas_profesor(curso)

def menu_editar_notas(estudiante, curso):
    # Menú para editar las notas de un estudiante
    while True:
        print(Fore.CYAN + f"\n== Notas de {estudiante['alumno']} ==\n")
        
        # Obtener las notas del curso desde la base de datos
        notas_curso = next((nota for nota in db.get('notas', []) if 'curso' in nota and nota['curso'] == curso['codigo_curso']), None)
        
        if not notas_curso:
            print(Fore.RED + "Error: No se encontraron datos de notas para este curso en la base de datos.")
            return
        
        # Obtener las notas específicas del alumno seleccionado
        notas_alumno = next((a for a in notas_curso['alumnos'] if a['alumno'] == estudiante['alumno']), None)
        
        if not notas_alumno:
            print(Fore.RED + "Este alumno no tiene notas registradas.\n")
            return
        
        # Mostrar las notas del alumno
        notas_lista = [[key, value] for key, value in notas_alumno.items() if key != 'alumno']
        print(Fore.GREEN + tabulate(notas_lista, headers=["Evaluación", "Calificación"], tablefmt='grid'))

        # Opciones del menú
        print("1. Registrar nota")
        print("2. Guardar cambios")
        print("3. Volver atrás")
        
        opcion = input(Fore.YELLOW + "Seleccione una opción: ").strip()

        if opcion == '1':
            registrar_nota(estudiante, curso, notas_alumno)
        elif opcion == '2':
            # Pasar los datos correctos al guardar
            guardar_cambios({
                'curso': curso['codigo_curso'],
                'alumno': estudiante['alumno'],
                **notas_alumno
            })
            break
        elif opcion == '3':
            return
        else:
            print(Fore.RED + "Opción inválida. Intenta nuevamente.\n")

def registrar_nota(estudiante, curso, notas_alumno):
    # Registrar una nueva nota solo si está pendiente
    print(Fore.CYAN + "== Registrar nota ==\n")
    materia = input(Fore.YELLOW + "Ingrese la evaluacion: ").strip()
    
    if materia not in notas_alumno:
        print(Fore.RED + "Evaluacion no encontrada en las notas del alumno.\n")
        return
    
    # Verificar si la nota está pendiente
    if notas_alumno[materia] != "Pendiente":
        print(Fore.RED + f"La evaluacion {materia} ya tiene una nota registrada.\n")
        return
    
    # Ingresar la nueva nota
    while True:
        try:
            nueva_nota = int(input(Fore.YELLOW + "Ingrese la nueva nota (de 0 a 20): ").strip())
            if 0 <= nueva_nota <= 20:
                notas_alumno[materia] = nueva_nota
                print(Fore.GREEN + f"Nota registrada para {materia}: {nueva_nota}\n")
                break
            else:
                print(Fore.RED + "La nota debe estar entre 0 y 20.\n")
        except ValueError:
            print(Fore.RED + "Por favor, ingrese un número válido.\n")
        
    return menu_editar_notas(estudiante, curso)

def guardar_cambios(notas_curso):

    print("Contenido de notas_curso:", notas_curso)

    # Validar que 'notas_curso' tiene las claves necesarias
    if not all(k in notas_curso for k in ['curso', 'alumno']):
        print(Fore.RED + "Error: 'notas_curso' no tiene las claves necesarias ('curso', 'alumno').")
        return

    print(Fore.GREEN + "Guardando cambios...\n")
    
    # Leer el archivo YAML
    try:
        with open("database.yaml", "r", encoding="utf-8") as file:
            db = yaml.safe_load(file)  # Cargar los datos existentes
    except FileNotFoundError:
        print(Fore.RED + "Error: El archivo YAML no se encuentra.")
        return
    except yaml.YAMLError as e:
        print(Fore.RED + f"Error al leer el archivo YAML: {e}")
        return

    # Buscar el bloque de notas para el curso correspondiente
    notas_actualizadas = False
    for curso_notas in db.get('notas', []):  # Iterar sobre el bloque 'notas'
        if curso_notas.get('curso') == notas_curso.get('curso'):  # Coincidir cursos
            for i, alumno in enumerate(curso_notas.get('alumnos', [])):
                # Validar la clave 'alumno' y comparar con notas_curso
                if alumno.get('alumno') == notas_curso.get('alumno'):
                    curso_notas['alumnos'][i] = deepcopy(notas_curso)  # Actualizar las notas
                    notas_actualizadas = True
                    break

    if notas_actualizadas:
        try:
            # Guardar las notas actualizadas en el archivo YAML
            with open("database.yaml", "w", encoding="utf-8") as file:
                yaml.safe_dump(db, file, default_flow_style=False, allow_unicode=True)
            print(Fore.GREEN + "Cambios guardados exitosamente.\n")
        except yaml.YAMLError as e:
            print(Fore.RED + f"Error al guardar el archivo YAML: {e}")
    else:
        print(Fore.RED + f"No se encontraron las notas para el curso: {notas_curso.get('curso')} y alumno: {notas_curso.get('alumno')}.\n")

#******************************************************************************************************************************************************

#Administrador **********************************************************************************************************************************************

def administrar_usuarios():
    while True:
        print("\n--- Menú de Administración de Usuarios ---")
        print("1. Listar usuarios")
        print("2. Crear usuario")
        print("3. Asignar usuario")
        print("4. Volver atrás")
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            listar_usuarios(db)  # Función para listar usuarios
        elif opcion == '2':
            crear_usuario()
        elif opcion == '3':
            asignar_usuario()
        elif opcion == '4':
            print("Volviendo al menú principal...")
            break
        else:
            print("Opción inválida. Intenta nuevamente.")

def listar_usuarios(db):
    # Filtrar los usuarios excluyendo al administrador (rol "Administrador")
    usuarios = [user for user in db['usuarios'] if user['rol'] != 'Administrador']
    
    # Preparar la tabla
    headers = ["Código", "Nombre", "Rol"]
    usuarios_data = [(user['codigo'], user['nombre'], user['rol']) for user in usuarios]
    
    # Mostrar la tabla
    print("\n--- Listado de Usuarios ---")
    print(tabulate(usuarios_data, headers=headers, tablefmt="grid"))
    print("\n")

def generar_mac_unica():
    # Generar una MAC única que no se repita
    while True:
        mac = f"44:11:{random.randint(0,99):02X}:{random.randint(0,99):02X}:{random.randint(0,99):02X}:{random.randint(0,99):02X}"
        if not any(user['mac'] == mac for user in db['usuarios']):  # Verificar que no exista
            return mac

def crear_usuario():
    print("\n--- Crear Usuario ---")
    
    # Seleccionar rol
    print("Seleccione el rol del nuevo usuario:")
    print("1. Estudiante")
    print("2. Profesor")
    opcion_rol = input("Seleccione una opción: ").strip()

    if opcion_rol == '1':
        rol = 'Estudiante'
    elif opcion_rol == '2':
        rol = 'Profesor'
    else:
        print("Opción inválida. Volviendo al menú principal.")
        return

    # Obtener información del usuario
    nombre = input("Ingrese el nombre del usuario: ").strip()
    codigo = input("Ingrese el código del usuario: ").strip()
    contrasenia = input("Ingrese la contraseña del usuario: ").strip()
    mac = generar_mac_unica()  # Generar una MAC única

    # Crear el usuario
    nuevo_usuario = {
        'codigo': int(codigo),
        'contrasenia': contrasenia,
        'mac': mac,
        'nombre': nombre,
        'rol': rol
    }

    # Agregar el nuevo usuario a la base de datos
    db['usuarios'].append(nuevo_usuario)

    # Guardar la base de datos actualizada en el archivo YAML
    guardar_base_datos(db)

    print(f"\nUsuario {nombre} creado con éxito!\n")

def guardar_base_datos(db):
    ruta = os.path.join(os.path.dirname(__file__), "database.yaml")
    with open(ruta, 'w', encoding="utf-8") as archivo:
        yaml.dump(db, archivo, default_flow_style=False, allow_unicode=True)
    print("Base de datos guardada en 'database.yaml'")

def asignar_usuario():
    while True:
        print("\n--- Menú de Asignación de Usuarios ---")
        print("1. Asignar profesor")
        print("2. Asignar estudiante")
        print("3. Volver atrás")
        
        opcion = input("Seleccione una opción: ").strip()

        if opcion == '1':
            asignar_profesor()
        elif opcion == '2':
            asignar_estudiante()
        elif opcion == '3':
            print("Volviendo al menú anterior...")
            break
        else:
            print("Opción inválida. Intenta nuevamente.")

def asignar_profesor():
    print("\n--- Asignar Profesor a un Curso ---")
    
    # Listar cursos con "Sin profesor"
    cursos_sin_profesor = [curso for curso in db['cursos'] if curso['profesor'] == "Sin profesor"]

    if not cursos_sin_profesor:
        print("Todos los cursos tienen asignado un profesor.")
        return

    print("\nCursos sin profesor:")
    headers = ["Código del Curso", "Nombre"]
    cursos_data = [[curso['codigo_curso'], curso['nombre']] for curso in cursos_sin_profesor]
    print(tabulate(cursos_data, headers=headers, tablefmt="grid"))

    # Listar profesores disponibles
    print("\nProfesores disponibles:")
    profesores = [user for user in db['usuarios'] if user['rol'] == 'Profesor']
    headers = ["Código", "Nombre"]
    profesores_data = [[profesor['codigo'], profesor['nombre']] for profesor in profesores]
    print(tabulate(profesores_data, headers=headers, tablefmt="grid"))

    # Solicitar asignación
    codigo_curso = input("\nIngrese el código del curso: ").strip()
    codigo_profesor = input("Ingrese el código del profesor: ").strip()

    curso = next((curso for curso in cursos_sin_profesor if curso['codigo_curso'] == codigo_curso), None)
    profesor = next((profesor for profesor in profesores if str(profesor['codigo']) == codigo_profesor), None)

    if not curso or not profesor:
        print("Código de curso o profesor inválido.")
        return

    # Asignar el profesor al curso
    curso['profesor'] = profesor['codigo']
    guardar_base_datos(db)
    print(f"Profesor {profesor['nombre']} asignado al curso {curso['nombre']} con éxito.")

def asignar_estudiante():
    print("\n--- Asignar Estudiante a un Curso ---")
    
    # Listar todos los cursos
    headers_cursos = ["Código del Curso", "Nombre"]
    cursos_data = [[curso['codigo_curso'], curso['nombre']] for curso in db['cursos']]
    print("\nCursos disponibles:")
    print(tabulate(cursos_data, headers=headers_cursos, tablefmt="grid"))

    # Listar estudiantes con cursos inscritos
    print("\nEstudiantes disponibles:")
    estudiantes = [user for user in db['usuarios'] if user['rol'] == 'Estudiante']
    headers_estudiantes = ["Código", "Nombre", "Cursos Inscritos"]
    estudiantes_data = []

    for estudiante in estudiantes:
        cursos_inscritos = [curso['nombre'] for curso in db['cursos'] if estudiante['codigo'] in curso['alumnos']]
        cursos_inscritos_str = ", ".join(cursos_inscritos) if cursos_inscritos else "Ninguno"
        estudiantes_data.append([estudiante['codigo'], estudiante['nombre'], cursos_inscritos_str])

    print(tabulate(estudiantes_data, headers=headers_estudiantes, tablefmt="grid"))

    # Solicitar asignación
    codigo_estudiante = input("\nIngrese el código del estudiante: ").strip()
    codigo_curso = input("Ingrese el código del curso: ").strip()

    curso = next((curso for curso in db['cursos'] if curso['codigo_curso'] == codigo_curso), None)
    estudiante = next((estudiante for estudiante in estudiantes if str(estudiante['codigo']) == codigo_estudiante), None)

    if not curso or not estudiante:
        print("Código de curso o estudiante inválido.")
        return

    # Verificar si el estudiante ya está inscrito
    if estudiante['codigo'] in curso['alumnos']:
        print("Este alumno ya se encuentra inscrito en el curso.")
        return

    # Confirmar la asignación
    confirmacion = input(f"¿Está seguro que desea agregar al alumno {estudiante['nombre']} (código {codigo_estudiante}) al curso {curso['nombre']} (código {codigo_curso})? [s/n]: ").strip().lower()
    if confirmacion == 's':
        curso['alumnos'].append(estudiante['codigo'])
        # Crear notas iniciales para el estudiante en este curso
        crear_seccion_notas(estudiante, curso)
        guardar_base_datos(db)
        print(f"Alumno {estudiante['nombre']} asignado al curso {curso['nombre']} con éxito.")
    else:
        print("Asignación cancelada.")

def crear_seccion_notas(estudiante, curso):
    print(f"Creando sección de notas para el alumno {estudiante['nombre']} en el curso {curso['nombre']}...")

    # Buscar las notas del curso
    notas_curso = next((notas for notas in db['notas'] if notas['curso'] == curso['codigo_curso']), None)
    if not notas_curso:
        print(f"No se encontraron notas registradas para el curso {curso['nombre']}.")
        return

    # Determinar el formato de las calificaciones basándose en otro alumno
    if notas_curso['alumnos']:
        formato_calificaciones = {k: "Pendiente" for k in notas_curso['alumnos'][0] if k != 'alumno'}
    else:
        print(f"El curso {curso['nombre']} no tiene formato de calificaciones definido.")
        return

    # Crear la entrada de notas para el nuevo estudiante
    nueva_nota = {'alumno': estudiante['codigo'], **formato_calificaciones}
    notas_curso['alumnos'].append(nueva_nota)

    print(f"Sección de notas creada para el alumno {estudiante['nombre']}.")

#******************************************************************************************************************************************************

# Función principal
def main():
    global db

    # Cargar base de datos
    db = cargar_base_datos()
    usuarios = db.get("usuarios", [])

    # Mostrar el banner
    mostrar_banner()

    # Login
    usuario_logueado = login(usuarios)

    # Mostrar menú correspondiente al rol
    while True:
        mostrar_menu(usuario_logueado, db)
        break

if __name__ == "__main__":
    main()