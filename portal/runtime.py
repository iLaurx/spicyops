"""Señal de salida compartida por la bandeja y la interfaz local autenticada."""
import threading
exit_requested = threading.Event()
