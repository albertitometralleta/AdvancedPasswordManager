# Gestor de Contraseñas Avanzado

Proyecto de gestor de contraseñas de escritorio seguro y fácil de usar, desarrollado en **Python** con **CustomTkinter**, que combina la protección tradicional de una clave maestra con la conveniencia y seguridad de la autenticación facial. Las contraseñas se almacenan de forma segura en un archivo `.csv` cifrado, utilizando una clave de cifrado que se guarda en una unidad USB externa para una capa de seguridad adicional.

---

## Características Principales

* **Cifrado Robusto**: Utiliza la librería `cryptography.fernet` para cifrar y descifrar las contraseñas, garantizando que tus datos sensibles no sean accesibles sin la clave de cifrado.
* **Autenticación en Dos Capas**: Accede a tus contraseñas mediante:
    * **Reconocimiento Facial** (método principal): Un método rápido y seguro para desbloquear el gestor utilizando la cámara de tu PC.
    * **Clave Maestra** (respaldo): Una contraseña segura en caso de que el reconocimiento facial falle o no esté disponible.
* **Portabilidad de la Clave**: La clave de cifrado (`clave.key`) se almacena en una unidad USB, lo que previene el acceso a tus contraseñas incluso si el archivo de datos está en un PC comprometido.
* **Interfaz Intuitiva**: Desarrollado con CustomTkinter, ofrece una interfaz de usuario moderna y amigable.
* **Gestión Completa**: Añade, actualiza y elimina contraseñas fácilmente.
* **Copia al Portapapeles**: Copia automáticamente las contraseñas al portapapeles, limpiándolas después de un tiempo para evitar filtraciones.

---

## Seguridad del Proyecto: Un Enfoque en Cifrado y Autenticación Biométrica

La seguridad de este proyecto se fundamenta en una estrategia de protección en dos frentes: el **cifrado de datos** y la **autenticación de usuario**. A continuación, se detallan los mecanismos y las tecnologías empleadas para asegurar que las contraseñas permanezcan a salvo.

---

### Protección de Datos con Fernet

El núcleo de la seguridad de los datos reside en la librería **`cryptography.fernet`**, un sistema de cifrado simétrico robusto. Fernet utiliza una clave única para cifrar y descifrar la información, asegurando que el contenido del archivo de contraseñas (`passwordsList.csv`) sea ilegible para cualquiera que no posea esta clave.

El proceso funciona de la siguiente manera:

1.  **Generación de la Clave**: Durante la configuración inicial, se genera una clave de cifrado (`clave.key`) que se guarda estratégicamente en una **unidad USB externa**. Este es un paso crítico, ya que la portabilidad de la clave evita que los datos puedan ser descifrados si el archivo `.csv` es extraído del ordenador, como en el caso de un ataque de malware o robo de dispositivo.

2.  **Cifrado del CSV**: Cuando el usuario cierra el gestor de contraseñas, la función `cifrar_csv` lee el contenido del archivo `passwordsList.csv`, lo encripta por completo con la clave Fernet y sobrescribe el archivo con la versión cifrada en formato binario.

3.  **Descifrado al Inicio**: Al iniciar la aplicación, la función `descifrar_csv` busca la clave en la USB, la carga y la utiliza para descifrar el contenido del archivo `passwordsList.csv`, permitiendo al programa acceder a la información en texto plano para su uso. Una vez finalizada la sesión, el archivo se vuelve a cifrar automáticamente.



Este método garantiza que incluso si el archivo de contraseñas es comprometido, los datos no podrán ser accedidos sin la clave que se encuentra físicamente en la unidad USB.

### Reconocimiento Facial: Un Proceso de Doble Etapa

La autenticación facial ofrece una capa de seguridad moderna y conveniente. Este sistema se basa en la inteligencia artificial y el procesamiento de imágenes para identificar al usuario de manera precisa.

El proceso se divide en dos fases principales:

#### 1. Entrenamiento del Modelo (Creación del Dataset)

* **Captura de Imágenes**: La función `create_dataset` utiliza la cámara del ordenador (`cv2.VideoCapture`) para capturar múltiples imágenes del rostro del usuario. Estas imágenes se convierten a escala de grises y se almacenan en una carpeta local (`faces/`).
* **Detección Facial**: El archivo pre-entrenado **`haarcascade_frontalface_default.xml`** de OpenCV juega un rol fundamental aquí. Este clasificador detecta las áreas de la imagen que se parecen a un rostro, permitiendo al programa recortar solo la cara del usuario de cada foto capturada.
* **Entrenamiento del Reconocedor**: La función `train_face_recognizer` entrena un modelo de reconocimiento facial con las imágenes capturadas. Se utiliza el algoritmo **LBPH (Local Binary Patterns Histograms)**, que analiza los patrones de textura y los mapea en un archivo de modelo (`trainer/trainer.yml`). Este archivo es, en esencia, la "huella digital" facial del usuario.

#### 2. Verificación del Usuario

* **Autenticación en Tiempo Real**: La función `verify_face` inicia la cámara y utiliza el modelo entrenado para predecir si el rostro en pantalla corresponde al perfil del usuario.
* **Predicción y Confianza**: El modelo predice un **ID** (en este caso, `1` para el usuario registrado) y un valor de **confianza**. Un valor de confianza bajo indica una alta probabilidad de que la persona sea el usuario correcto.
* **Validación con Umbral**: Se establece un umbral de confianza (`confidence_threshold = 60`). Si el modelo predice el ID correcto y la confianza está por debajo de este umbral durante un tiempo sostenido (3 segundos), la autenticación se considera exitosa. En caso contrario, el acceso es denegado.

Este enfoque de dos pasos garantiza que la autenticación sea tanto precisa como segura, proporcionando una experiencia de usuario fluida sin comprometer la integridad del sistema.

---

## Requisitos

* Asegúrate de tener instaladas las siguientes librerías de Python. Puedes instalarlas con `requirements.txt`
* Python 3.12.10 o superior
* Windows 10/11

---

## Configuración Inicial

1. Instala las dependencias de `requirements.txt`

2. Conecta una unidad USB a tu ordenador. El programa detectará la primera unidad extraíble que encuentre.

3. Ejecuta el script principal: main_gui.py.

4. Si es la primera vez que lo ejecutas, la aplicación te guiará a través de un proceso de configuración inicial:

    - Se creará la clave de cifrado clave.key en tu unidad USB.

    - Se te pedirá que crees una Clave Maestra.

    - Se iniciará un proceso de captura facial para crear tu perfil de reconocimiento. Asegúrate de mirar directamente a la cámara.

---

## Uso 

### Desbloquear la Aplicación

Al iniciar la aplicación, se te pedirá que te autentiques. El método predeterminado es el reconocimiento facial. Simplemente mira a la cámara y espera a que el sistema te reconozca.

Si prefieres usar tu clave maestra, haz clic en el botón de la parte inferior para cambiar al modo de contraseña.

### Interfaz Principal

Una vez desbloqueada, verás la interfaz principal. A la izquierda, tienes los botones de acción para añadir contraseñas o modificar tu perfil. A la derecha, se muestra la lista de todas tus contraseñas guardadas.

### Gestionar Contraseñas

* Añadir Contraseña: Haz clic en Add Password y sigue las instrucciones para guardar un nuevo sitio, usuario y contraseña. El programa cifrará y guardará la información automáticamente.

* Ver, Copiar y Borrar: Cada entrada en la lista tiene tres botones:

    - 👁️: Muestra u oculta la contraseña.

    - 📋: Copia la contraseña al portapapeles. La contraseña se borrará automáticamente después de 15 segundos.

    - 🗑️: Elimina la entrada.

---

##  Estructura del Proyecto

* `main_gui.py`: El script principal que maneja la interfaz de usuario (GUI), la lógica de la aplicación y el flujo de autenticación.

* `utils.py`: Contiene todas las funciones de "backend" para la gestión de archivos, cifrado, reconocimiento facial y utilidades del sistema. Esto mantiene el código principal limpio y organizado.

* `passwordsList.csv`: El archivo donde se almacenan tus contraseñas. Se cifra automáticamente al cerrar la aplicación y se descifra al abrirla.

* `haarcascade_frontalface_default.xml`: Clasificador pre-entrenado de OpenCV. Es un archivo XML que contiene datos de entrenamiento para la detección de rostros frontales. 

* `requirements.txt`: Archivo donde se hallan las dependencias necesarias para la ejecución del programa.

* `faces/`: Carpeta donde se guardan las imágenes capturadas para el entrenamiento facial.

* `trainer/` : Carpeta donde se guardará el modelo de reconocimiento facial entrenado.

### Archivos de Seguridad y Datos

* `clave.key`: La clave de cifrado fundamental. Se genera al inicio y se guarda en la unidad USB. 

* `master.key`: Almacena el hash de tu clave maestra para la validación.

---

## ADVERTENCIA

* **No pierdas tu USB**: La clave de cifrado (clave.key) es indispensable para descifrar tus contraseñas. Si pierdes la unidad USB con la clave, no podrás recuperar tus datos.

* **Guarda la clave maestra en un lugar seguro**: La clave maestra es tu respaldo en caso de que el reconocimiento facial falle.