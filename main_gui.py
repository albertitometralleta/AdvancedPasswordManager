import customtkinter as ctk
from tkinter import messagebox
import utils  
import os
import pyperclip
import pandas as pd
import cv2

# Configuramos la apariencia inicial
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")  

class PasswordManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ---
        self.title("Password Manager")
        self.geometry("800x550")
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Acción al cerrar

        # --- VARIABLES DE ESTADO ---
        self.usb_path = None # Ruta del USB detectado
        self.key_path = None # Ruta del archivo de clave
        self.passwords_decrypted = False # Indica si las contraseñas han sido descifradas
        self.username = None # Nombre de usuario para reconocimiento facial

        # --- Cargar modelos de IA al inicio ---
        self._load_models()

        # --- INICIO DE LA APLICACIÓN ---
        self.check_initial_setup()

    def _load_models(self):
        """Carga los modelos de IA una sola vez y los almacena en la instancia."""
        
        self.face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists('trainer/trainer.yml'):
            self.recognizer.read('trainer/trainer.yml')
        print("Modelos cargados con exito.")

    def check_initial_setup(self):
        """
        Verifica si los archivos de clave existen. Si no, guía al usuario
        para crearlos. Si existen, muestra la pantalla de login.
        """
        # 1. Detectar USB
        usb_drives = utils.detectar_usb()
        if not usb_drives:
            messagebox.showerror("Critical Error", "Any USB drive detected.\nPlease insert a USB drive with 'clave.key' file.")
            self.quit()
            return
        
        # Usamos la primera unidad USB encontrada
        self.usb_path = usb_drives[0]
        self.key_path = os.path.join(self.usb_path, 'clave.key')
        utils.RUTA_CLAVE = self.key_path # Actualizamos la ruta en utils
        passwords_file = 'passwordsList.csv'

        # 2. Si no existe clave.key en el USB
        if not os.path.exists(self.key_path):
            # Verificamos si el CSV existe y tiene datos
            if not os.path.exists(passwords_file) or os.stat(passwords_file).st_size == 0:
                # No hay contraseñas -> crear clave automáticamente
                utils.create_key(self.key_path)
                messagebox.showinfo("New Key Created", f"No key found. A new key has been generated at:\n{self.key_path}", parent=self)
            else:
                # Archivo existe y tiene datos -> pedir confirmación
                resp = messagebox.askyesno(
                    "Key Missing",
                    "No 'clave.key' file was found in the USB.\nHowever, existing passwords were detected.\n"
                    "Do you want to generate a NEW key? (This will ERASE all saved passwords!)"
                )
                if resp:
                    utils.create_key(self.key_path)
                    # Vaciar el CSV
                    with open(passwords_file, 'w') as f:
                        f.write('SITE,USER,PASSWORD\n')
                    messagebox.showinfo("Reset Complete", "New key generated and passwords list cleared.", parent=self)
                else:
                    messagebox.showerror("Operation Cancelled", "No key created. Application will close.", parent=self)
                    self.quit()
                    return

         # 3. Comprobar si es la primera ejecución 
        if not os.path.exists('master.key'):
            # --- FLUJO DE CONFIGURACIÓN INICIAL ---
            self.deiconify() # Mostramos la ventana para los diálogos

            # Crear clave maestra
            new_pass = ctk.CTkInputDialog(text="Welcome! Please create a new Master Key:", title="Create Master Key").get_input()
            if not new_pass: self.quit(); return
            utils.create_master_key(new_pass)
            
            # Pedir nombre de usuario
            self.username = ctk.CTkInputDialog(text="Now, please enter your name for facial recognition:", title="Enter Name").get_input()
            if not self.username: self.quit(); return
            utils.save_username(self.username)

            # Iniciar captura y entrenamiento facial
            messagebox.showinfo("Face Capture", "Next, we will capture 30 images of your face.\nPlease look at the camera and hold still.", parent=self)
            #self.withdraw() # Ocultamos la ventana principal durante la captura
            utils.create_dataset(self.face_cascade)
            utils.train_face_recognizer()
            #self.deiconify() # Volvemos a mostrarla
            messagebox.showinfo("Setup Complete", "Your facial profile has been created successfully!", parent=self)
            self.recognizer.read('trainer/trainer.yml')

        self.show_login_screen()

    def show_login_screen(self):
        """Muestra la pantalla de inicio de sesión facial como método principal."""
        #self.deiconify()

        self.face_login_frame = ctk.CTkFrame(self)
        self.face_login_frame.pack(pady=20, padx=60, fill="both", expand=True)

        label = ctk.CTkLabel(self.face_login_frame, text="Facial Recognition Login", font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=40)

        scan_button = ctk.CTkButton(self.face_login_frame, text="Scan Face to Unlock", command=self.handle_face_login, height=40)
        scan_button.pack(pady=20, padx=20, fill="x")

        password_button = ctk.CTkButton(self.face_login_frame, text="Login with Master Key instead", fg_color="transparent", command=self.show_password_login_screen)
        password_button.pack(pady=10)
    
    def handle_face_login(self):
        """Gestiona el proceso de verificación facial."""
        username = utils.load_username()
        if not username:
            messagebox.showerror("Error", "Username not found. Please log in with Master Key to set up Face ID.", parent=self)
            self.show_password_login_screen()
            return
        
        messagebox.showinfo("Face Scan", "The camera will now open.\nPlease look directly at it.", parent=self)
        
        self.withdraw() # Ocultar GUI durante el escaneo
        user_id = utils.verify_face(username, self.face_cascade, self.recognizer)
        self.deiconify() # Mostrar GUI de nuevo
        
        if user_id == 1:
            messagebox.showinfo("Success", "Face recognized successfully!", parent=self)
            self.unlock_app()
        else:
            messagebox.showwarning("Failed", "Face not recognized. Please try again or use your Master Key.", parent=self)

    def show_password_login_screen(self):
        """Muestra la pantalla de login con contraseña como alternativa."""
        # Destruir el frame de login facial si existe
        if hasattr(self, 'face_login_frame'):
            self.face_login_frame.destroy()

        self.password_login_frame = ctk.CTkFrame(self)
        self.password_login_frame.pack(pady=20, padx=60, fill="both", expand=True)

        label = ctk.CTkLabel(self.password_login_frame, text="Enter your Master Key", font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=40)

        self.master_password_entry = ctk.CTkEntry(self.password_login_frame, show="*", width=300)
        self.master_password_entry.pack(pady=10)
        self.master_password_entry.bind("<Return>", self.handle_password_login)

        login_button = ctk.CTkButton(self.password_login_frame, text="Unlock", command=self.handle_password_login)
        login_button.pack(pady=20) 
    
    def handle_password_login(self, event=None):
        """Valida la contraseña maestra."""
        password = self.master_password_entry.get()
        if utils.validate_master_key(password):
            self.unlock_app()
        else:
            messagebox.showerror("Error", "Incorrect Master Key.", parent=self)
            self.master_password_entry.delete(0, 'end')

    def unlock_app(self):
        """Acciones a realizar tras un login exitoso (facial o por contraseña)."""
        # Destruir frames de login
        if hasattr(self, 'face_login_frame'): self.face_login_frame.destroy()
        if hasattr(self, 'password_login_frame'): self.password_login_frame.destroy()

        # Descifrar CSV
        if os.path.exists('passwordsList.csv'):
            try:
                utils.descifrar_csv('passwordsList.csv', self.key_path)
                self.passwords_decrypted = True
            except Exception as e:
                messagebox.showerror("Decryption Error", f"The key on the USB is not valid for this file or it is corrupt.\nError: {e}", parent=self)
                self.quit()
                return
        
        self.show_main_ui()

    def show_main_ui(self):
        """Crea la interfaz principal del gestor de contraseñas."""
        # --- LAYOUT PRINCIPAL (IZQUIERDA: ACCIONES, DERECHA: LISTA) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- FRAME IZQUIERDO PARA BOTONES Y ACCIONES ---
        left_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(left_frame, text="Actions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        ctk.CTkButton(left_frame, text="Add Password", command=self.add_password).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(left_frame, text="Update Face ID", 
              fg_color="transparent", 
              border_width=2, 
              text_color=("gray10", "#DCE4EE"), 
              command=self.handle_retrain_face).pack(pady=10, padx=20, fill="x")


        ctk.CTkButton(left_frame, text="Change Master Key", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.change_master_key).pack(pady=(20, 10), padx=20, fill="x")

        # --- FRAME DERECHO PARA LA LISTA DE CONTRASEÑAS ---
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right_frame, text="My Passwords", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        
        # --- Cabeceras de la tabla ---
        header_frame = ctk.CTkFrame(right_frame, corner_radius=0, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,0))
        header_frame.grid_columnconfigure(0, weight=3) # Site
        header_frame.grid_columnconfigure(1, weight=3) # User
        header_frame.grid_columnconfigure(2, weight=2) # Password
        header_frame.grid_columnconfigure(3, weight=1) # Actions

        ctk.CTkLabel(header_frame, text="Site", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0)
        ctk.CTkLabel(header_frame, text="Username", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1)
        ctk.CTkLabel(header_frame, text="Password", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2)

        # --- Contenedor de contraseñas con scroll ---
        self.scrollable_frame = ctk.CTkScrollableFrame(right_frame, label_text="My Passwords")
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.load_passwords_ui()

    def load_passwords_ui(self):
        """Carga las contraseñas en la UI, creando una fila para cada una."""
        # Limpiar vista anterior
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not os.path.exists('passwordsList.csv'):
            return
        utils.ensure_passwords_file('passwordsList.csv')  # Aseguramos que el archivo existe y tiene encabezados
        df = pd.read_csv('passwordsList.csv')
        # Obtenemos los datos descifrados para construir la UI
        clave_obj = utils.Fernet(utils.cargar_clave(self.key_path))

        for index, row in df.iterrows():
            site = row['SITE']
            # Desciframos los datos reales para usarlos en los botones
            try:
                user = clave_obj.decrypt(row['USER'].encode()).decode()
                password = clave_obj.decrypt(row['PASSWORD'].encode()).decode()
            except Exception:
                # Si una fila está corrupta, se muestra pero no se podrá interactuar
                user = "Data Error"
                password = "N/A"

            # --- Crear una fila para esta contraseña ---
            row_frame = ctk.CTkFrame(self.scrollable_frame)
            row_frame.pack(fill="x", pady=5, padx=5)
            row_frame.grid_columnconfigure((0, 1), weight=3)
            row_frame.grid_columnconfigure(2, weight=2)
            row_frame.grid_columnconfigure((3, 4, 5), weight=0) # Botones

            # Labels para Site y User
            ctk.CTkLabel(row_frame, text=site, anchor="w").grid(row=0, column=0, sticky="ew", padx=5)
            ctk.CTkLabel(row_frame, text=user, anchor="w").grid(row=0, column=1, sticky="ew", padx=5)
            
            # Label para la contraseña (que se podrá cambiar)
            password_label = ctk.CTkLabel(row_frame, text="********", anchor="w")
            password_label.grid(row=0, column=2, sticky="ew", padx=5)

            # --- Botones de acción en la fila ---
            def toggle_visibility(label=password_label, pwd=password):
                if label.cget("text") == "********":
                    label.configure(text=pwd)
                else:
                    label.configure(text="********")

            def copy_password(pwd=password):
                pyperclip.copy(pwd)
                messagebox.showinfo("Copied", "Password copied to clipboard (15s).", parent=self)
                self.after(15000, pyperclip.copy, "")
            
            def delete_entry(site_to_delete=site):
                if messagebox.askyesno("Confirm", f"Delete entry for '{site_to_delete}'?", parent=self):
                    utils.delete_password(site_to_delete)
                    self.load_passwords_ui() # Recargar la lista

            ctk.CTkButton(row_frame, text="👁️", width=30, command=toggle_visibility).grid(row=0, column=3, padx=2)
            ctk.CTkButton(row_frame, text="📋", width=30, command=copy_password).grid(row=0, column=4, padx=2)
            ctk.CTkButton(row_frame, text="🗑️", width=30, fg_color="#DB3E3E", hover_color="#B83232", command=delete_entry).grid(row=0, column=5, padx=(2,5))

    def add_password(self):
        """Abre un diálogo para añadir o actualizar una contraseña."""
        dialog = ctk.CTkInputDialog(text="Enter the name of the SITE:", title="Add/Update Password")
        site = dialog.get_input()
        if not site: return

        dialog = ctk.CTkInputDialog(text=f"Enter the username for '{site}':", title="Add Username")
        user = dialog.get_input()
        if not user: return
        
        dialog = ctk.CTkInputDialog(text=f"Enter password for '{site}':", title="Add Password")
        password = dialog.get_input()
        if not password: return

        # Guardamos usando la función de utils
        clave_obj = utils.Fernet(utils.cargar_clave(self.key_path))
        utils.save_passwords_to_csv(site, user, password, clave_obj)
        messagebox.showinfo("Success", f"Password for '{site}' saved successfully.")
        self.load_passwords_ui() # Recargamos la nueva UI
    
    def change_master_key(self):
        """Permite al usuario cambiar su clave maestra."""
        new_pass = ctk.CTkInputDialog(text="Enter your NEW master key", title="Change Master Key").get_input()
        if new_pass:
            confirm_pass = ctk.CTkInputDialog(text="Confirm your NEW master key:", title="Confirm key").get_input()
            if new_pass == confirm_pass:
                utils.modify_master_key(new_pass)
                messagebox.showinfo("Success", "Your master key has been changed successfully.")
            else:
                messagebox.showerror("Error", "The passwords do not match.")

    def on_closing(self):
        """
        Se ejecuta al cerrar la ventana. Cifra el archivo de contraseñas
        y cierra la aplicación.
        """
        if self.passwords_decrypted:
            if messagebox.askyesno("Exit", "Are you sure you want to exit?\nThe password file will be encrypted."):
                utils.cifrar_csv('passwordsList.csv', self.key_path)
                self.destroy()
        else:
            self.destroy()

    def handle_retrain_face(self):
        """Gestiona el reentrenamiento del reconocimiento facial."""
        confirm = messagebox.askyesno("Update Face ID", "This will delete your existing face data and start a new capture process. Are you sure?", parent=self)
        if confirm:
            utils.delete_user_images()
            messagebox.showinfo("Face Capture", "Next, we will capture 30 new images of your face.\nPlease look at the camera and hold still.", parent=self)
            self.withdraw()
            utils.create_dataset(self.face_cascade)
            utils.train_face_recognizer()
            self.deiconify()
            messagebox.showinfo("Success", "Your facial profile has been updated!", parent=self)

if __name__ == "__main__":
    # Realizamos las comprobaciones críticas ANTES de crear la ventana principal
    if not os.path.exists("haarcascade_frontalface_default.xml"):
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror("Missing File", "Error: 'haarcascade_frontalface_default.xml' not found.\nPlease download it and place it in the application folder.")
    elif not utils.detectar_usb():
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror("Critical Error", "No USB drive detected.\nPlease insert a USB drive with 'clave.key' file.")
    else:
        # Si todo está en orden, iniciamos la aplicación
        app = PasswordManagerApp()
        app.mainloop()