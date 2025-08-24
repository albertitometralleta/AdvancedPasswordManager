import pandas as pd
import os
import hashlib
from cryptography.fernet import Fernet
import cv2
import psutil
import numpy as np
import time
from PIL import Image


RUTA_CLAVE = './clave.key'
MASTER_KEY = './master.key'


#------------------------------------------------------------------------------------------------------------------------------

"""Cargar la clave de cifrado desde un archivo"""
def cargar_clave(path=RUTA_CLAVE):
    with open(path, 'rb') as f:
        return f.read()
    
#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para guardar contraseñas en un archivo CSV cifradas"""
def save_passwords_to_csv(site, user, password, fernet, filename='passwordsList.csv'):
    password_cifrada = fernet.encrypt(password.encode()).decode()
    user_cifrado = fernet.encrypt(user.encode()).decode()
    nueva_fila = {'SITE': site, 'USER': user_cifrado, 'PASSWORD': password_cifrada}

    if os.path.exists(filename):
        ensure_passwords_file('passwordsList.csv')
        df = pd.read_csv(filename)
        if site in df['SITE'].values:
            df.loc[df['SITE'] == site, ['USER', 'PASSWORD']] = [user_cifrado, password_cifrada]
        else:
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    else:
        df = pd.DataFrame([nueva_fila])

    df.to_csv(filename, index=False)
    print(f"Contraseña guardada para el sitio '{site}'.")
    return True

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para consultar contraseñas"""
def consult_passwords(site, filename='passwordsList.csv'):
    if os.path.exists(filename):
        ensure_passwords_file('passwordsList.csv')
        df = pd.read_csv(filename)
        if site in df['SITE'].values:
            row = df[df['SITE'] == site].iloc[0]
            user_cifrado = row['USER']
            password_cifrada = row['PASSWORD']
            clave = cargar_clave(RUTA_CLAVE)
            fernet = Fernet(clave)
            user = fernet.decrypt(user_cifrado.encode()).decode()
            password = fernet.decrypt(password_cifrada.encode()).decode()
            return {'SITE': site, 'USER': user, 'PASSWORD': password}
    else:
        print("El archivo de contraseñas no existe.")
        return None

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para asegurar que el archivo de contraseñas existe y tiene los encabezados correctos"""
def ensure_passwords_file(filename='passwordsList.csv'):
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        # Crear archivo con encabezados
        with open(filename, 'w') as f:
            f.write('SITE,USER,PASSWORD\n')

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para eliminar una contraseña"""
def delete_password(site, filename='passwordsList.csv'):
    if os.path.exists(filename):
        ensure_passwords_file('passwordsList.csv')
        df = pd.read_csv(filename)
        if site in df['SITE'].values:
            df = df[df['SITE'] != site]
            df.to_csv(filename, index=False)
            print(f"Contraseña eliminada para el sitio '{site}'.")
            return True
        else:
            print(f"No se encontró el sitio '{site}' en la lista de contraseñas.")
            return False
    else:
        print("El archivo de contraseñas no existe.")
        return False

#------------------------------------------------------------------------------------------------------------------------------

"""Función para crear una clave de cifrado y guardarla en un archivo"""
def create_key(path='clave.key'):
    clave = Fernet.generate_key()
    with open(path, 'wb') as f:
        f.write(clave)
    RUTA_CLAVE = path
    print(f"Clave generada y guardada en {RUTA_CLAVE}.")

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para generar una clave maestra"""
def create_master_key(password, path='./master.key'):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with open(path, 'w') as f:
        f.write(hashed_password)
    MASTER_KEY = path
    print(f"Clave generada y guardada en {MASTER_KEY}.")

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para modificar la clave maestra"""
def modify_master_key(new_password, path=MASTER_KEY):
    # Calcular el hash SHA-256 de la nueva contraseña
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    
    # Escribir (sobrescribir) el hash en el archivo
    try:
        with open(path, 'w') as f:
            f.write(hashed_password)
        print(f"Clave maestra actualizada correctamente en '{path}'.")
    except Exception as e:
        print(f"Error al modificar la clave maestra: {e}")
    

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para validar la clave maestra"""
def validate_master_key(in_password, path=MASTER_KEY):
    hashed_in_password = hashlib.sha256(in_password.encode()).hexdigest()

    if not os.path.exists(path):
        print("El archivo con la clave maestra no existe.")
        return False

    try:
        with open(path, 'r') as f:
            stored_hash = f.read().strip()

        return hashed_in_password == stored_hash
    except Exception as e:
        print(f"Error al validar la clave maestra: {e}")
        return False

#------------------------------------------------------------------------------------------------------------------------------

"""Función para cifrar el archivo CSV de contraseñas"""
def cifrar_csv(filename='passwordsList.csv', clave_path=RUTA_CLAVE):
    # Cargar la clave de cifrado
    clave = cargar_clave(clave_path)
    fernet = Fernet(clave)
    
    # Leer el contenido del CSV como texto
    with open(filename, 'rb') as file:
        contenido = file.read()
    
    # Cifrar el contenido
    contenido_cifrado = fernet.encrypt(contenido)
    
    # Sobrescribir el archivo con el contenido cifrado
    with open(filename, 'wb') as file:
        file.write(contenido_cifrado)
    
    print(f"Archivo {filename} cifrado exitosamente.")

#-------------------------------------------------------------------------------------------------------------------------------

"""Función para descifrar el archivo CSV de contraseñas"""
def descifrar_csv(filename='passwordsList.csv', clave_path=RUTA_CLAVE):
    clave = cargar_clave(clave_path)
    fernet = Fernet(clave)

    with open(filename, 'rb') as file:
        contenido_cifrado = file.read()

    try:
        contenido = fernet.decrypt(contenido_cifrado).decode()  # convertimos a str
    except Exception as e:
        print("Error al descifrar:", e)
        return

    # Guardar el contenido descifrado como texto
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(contenido)
    
    print(f"Archivo {filename} descifrado exitosamente.")

#------------------------------------------------------------------------------------------------------------------------------

"""Función para capturar imágenes de la cara del usuario y guardarlas en un directorio"""
def create_dataset(face_detector):
    # Crear el directorio para guardar las imágenes si no existe
    if not os.path.exists('faces'):
        os.makedirs('faces')

    # Iniciar la captura de video
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 640) 
    cam.set(4, 480) 


    print("\n Inicializando captura de cara. Mira a la cámara y espera ...")

    # Inicializar el contador de imágenes capturadas
    count = 0

    while True:
        ret, img = cam.read()
        if not ret:
            print("Error: No se pudo capturar la imagen de la cámara.")
            break
            
        # Convertir la imagen a escala de grises (es mejor para el reconocimiento)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detectar caras en la imagen
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Dibujar un rectángulo alrededor de la cara
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            count += 1

            # Guardar la imagen de la cara capturada en la carpeta 'faces'
            cv2.imwrite(os.path.join("faces", f"User.1.{count}.jpg"), gray[y:y+h, x:x+w])

            # Mostrar la imagen en una ventana
            cv2.imshow('image', img)

        # Esperar 100 ms o hasta que se presione la tecla ESC
        k = cv2.waitKey(100) & 0xff
        if k == 27: # Tecla ESC para salir
            break
        elif count >= 50: # Tomar 50 muestras de la cara y salir
            break

    print("\n Saliendo del programa y limpiando...")
    cam.release()
    cv2.destroyAllWindows()

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para entrenar el reconocedor de caras usando las imágenes capturadas y un dataset de caras"""
def train_face_recognizer():
    # Ruta a la carpeta con las imágenes de las caras
    path = 'faces'

    # Crear el reconocedor usando el algoritmo LBPH
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    # Función para obtener las imágenes y las etiquetas
    def getImagesAndLabels(path):
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []

        for imagePath in imagePaths:
            # Abrir la imagen y convertirla a escala de grises
            PIL_img = Image.open(imagePath).convert('L') 
            img_numpy = np.array(PIL_img, 'uint8')

            # Extraer el ID de usuario del nombre del archivo
            filename = os.path.basename(imagePath)  

            if filename.startswith("User"):
                # Caso especial: 
                id = int(os.path.split(imagePath)[-1].split(".")[1])
            else:
                # En cualquier otro caso, usamos el nombre del archivo (sin extensión)
                id_str = os.path.splitext(filename)[0]  
                id = int(id_str)   
                
            # Detectar la cara en la imagen
            faces = detector.detectMultiScale(img_numpy)

            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y+h, x:x+w])
                ids.append(id)

        return faceSamples, ids

    print("\n Entrenando el modelo con las caras. Esto puede tardar unos segundos. Espera...")
    faces, ids = getImagesAndLabels(path)
    recognizer.train(faces, np.array(ids))

    # Crear la carpeta 'trainer' si no existe
    if not os.path.exists('trainer'):
        os.makedirs('trainer')

    # Guardar el modelo entrenado
    recognizer.write('trainer/trainer.yml')

    print(f"\n {len(np.unique(ids))} caras entrenadas. Saliendo del programa.")

#------------------------------------------------------------------------------------------------------------------------------

"""Función para verificar el rostro del usuario usando la cámara """
def verify_face(username, faceCascade, recognizer):
    font = cv2.FONT_HERSHEY_SIMPLEX
    names = ['None', username] 
    cam = cv2.VideoCapture(00, cv2.CAP_DSHOW)
    cam.set(3, 640) 
    cam.set(4, 480) 
    minW = 0.1 * cam.get(3)
    minH = 0.1 * cam.get(4)
    
    recognized_id = 0 
    recognized_time = None

    while True:
        ret, img = cam.read()
        if not ret:
            print("Error: No se pudo acceder a la cámara.")
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            
            confidence_threshold = 60

            #Comprueba si la confianza es suficientemente buena (valor bajo) Y si el ID es el correcto (1)
            if confidence < confidence_threshold and id == 1:
                id_name = names[id] # Asigna nombre de usuario
                
                # Si es la primera vez que te reconoce, guarda el tiempo
                if recognized_time is None:
                    recognized_time = time.time()
                    recognized_id = 1 # Guarda el ID correcto para devolverlo al final
            else:
                # Si la confianza es mala (valor alto) o el ID no es 1, es un desconocido
                id_name = "Unknown"
                recognized_id = 0 

            # Mostrar el nombre 
            cv2.putText(img, str(id_name), (x + 5, y - 5), font, 1, (255, 255, 255), 2)

        cv2.imshow('camera', img)

        # Si han pasado 3 segundos desde un reconocimiento exitoso, salimos
        if recognized_time is not None and (time.time() - recognized_time) >= 3:
            print(f"\nUsuario {username} reconocido. Cerrando...")
            break

        k = cv2.waitKey(10) & 0xff 
        if k == 27: # Salir con la tecla ESC
            recognized_id = 0 # Si el usuario sale manualmente, no se considera exitoso
            break

    print("\n Saliendo del programa.")
    cam.release()
    cv2.destroyAllWindows()
    
    # Devuelve el ID solo si el reconocimiento fue exitoso y continuo
    return recognized_id
#------------------------------------------------------------------------------------------------------------------------------

"""Función para detectar unidades USB conectadas"""
def detectar_usb():
    usb_paths = []
    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        if 'removable' in p.opts.lower():  # Filtrar unidades extraíbles
            usb_paths.append(p.device)
    return usb_paths

#------------------------------------------------------------------------------------------------------------------------------

"""Funcion para borrar las antiguas imágenes de usuario en la carpeta 'faces'"""
def delete_user_images(folder="faces"):
    if not os.path.exists(folder):
        print(f"La carpeta '{folder}' no existe.")
        return
    
    count = 0
    for filename in os.listdir(folder):
        if filename.startswith("User") and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(folder, filename)
            try:
                os.remove(filepath)
                count += 1
            except Exception as e:
                print(f"Error al borrar {filepath}: {e}")

#-------------------------------------------------------------------------------------------------------------------------------

"""Función para guardar el nombre de usuario en un archivo"""
def save_username(username, filename="username.dat"):
    with open(filename, "w") as f:
        f.write(username)
    print(f"Nombre de usuario '{username}' guardado.")

#-------------------------------------------------------------------------------------------------------------------------------

"""Función para cargar el nombre de usuario desde un archivo"""
def load_username(filename="username.dat"):
    if not os.path.exists(filename):
        return None
    with open(filename, "r") as f:
        return f.read().strip()
    



