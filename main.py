# main.py
# (Modificado con lógica de IP Estática primero)

import sys
import time
import requests
import socket
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QApplication
from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
from GUI.gui import Ui_MainWindow


# --- PARTE 1: LÓGICA DE DETECCIÓN (Sin cambios) ---
class ArduinoListener(ServiceListener):
    def __init__(self):
        self.arduino_info = None

    def add_service(self, zc, type_, name):
        if "sistemaclima-tecnm" in name:
            info = zc.get_service_info(type_, name)
            if info:
                ip_address = socket.inet_ntoa(info.addresses[0])
                self.arduino_info = {"ip": ip_address}
                print(f"[Discovery] Arduino encontrado en: {ip_address}")

    def update_service(self, zc, type_, name):
        pass

    def remove_service(self, zc, type_, name):
        pass


class DiscoveryWorker(QtCore.QObject):
    found = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def run(self):
        zeroconf = Zeroconf()
        listener = ArduinoListener()
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        time.sleep(5)
        browser.cancel()
        zeroconf.close()
        self.found.emit(listener.arduino_info if listener.arduino_info else {})
        self.finished.emit()


# --- PARTE 2: LÓGICA DEL WORKER DE DATOS (Sin cambios) ---
class ArduinoWorker(QtCore.QObject):
    datos_actualizados = QtCore.pyqtSignal(dict)
    error_ocurrido = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, arduino_ip):
        super().__init__()
        self.arduino_url = f"http://{arduino_ip}/data"
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                response = requests.get(self.arduino_url, timeout=2.5)
                response.raise_for_status()
                data = response.json()
                self.datos_actualizados.emit(data)
                time.sleep(1)
            except Exception as e:
                print(f"[ArduinoWorker Error]: {e}")
                self.error_ocurrido.emit(f"Error: {type(e).__name__}")
                time.sleep(5)
        self.finished.emit()

    def stop(self):
        self.is_running = False


# --- PARTE 3: LA APLICACIÓN PRINCIPAL (MODIFICADA) ---
class EstacionApp(Ui_MainWindow):
    def __init__(self):
        super().__init__()

        # --- NUEVO: IP Estática ---
        # ¡CAMBIA ESTA IP POR LA IP ESTÁTICA DE TU ARDUINO!
        self.ARDUINO_STATIC_IP = "192.168.3.100"

        self.arduino_ip = None
        self.data_thread = None

        # Listas para el gráfico (sin cambios)
        self.max_points = 50
        self.time_data = []
        self.temp_data = []
        self.hum_data = []
        self.x_counter = 0

        self.iniciar_timer_reloj()

        # --- LÓGICA DE CONEXIÓN MODIFICADA ---
        # 1. Conectar el botón "BUSCAR IP" (Método 2: Auto-Discovery)
        self.search_btn.clicked.connect(self.iniciar_busqueda_arduino)

        # 2. Iniciar la conexión estática (Método 1) INMEDIATAMENTE
        self.iniciar_conexion_automatica()

    # --- NUEVO MÉTODO ---
    def iniciar_conexion_automatica(self):
        """
        Método 1: Intenta conectarse a la IP estática al iniciar.
        """
        self.statusBar().showMessage(f"Intentando conexión automática a IP estática: {self.ARDUINO_STATIC_IP}...")
        self.arduino_ip = self.ARDUINO_STATIC_IP
        self.ip_display.setText(self.arduino_ip)

        # Deshabilitar el botón de búsqueda mientras se intenta conectar
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Conectando...")

        self.iniciar_hilo_trabajador()

    def iniciar_busqueda_arduino(self):
        """
        Método 2: Inicia la auto-detección (Zeroconf) al pulsar el botón.
        """
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Buscando...")
        self.statusBar().showMessage("Buscando Arduino en la red...")

        self.discovery_thread = QtCore.QThread()
        self.discovery_worker = DiscoveryWorker()
        self.discovery_worker.moveToThread(self.discovery_thread)

        self.discovery_thread.started.connect(self.discovery_worker.run)
        self.discovery_worker.found.connect(self.on_discovery_complete)
        self.discovery_worker.finished.connect(self.discovery_thread.quit)
        self.discovery_worker.finished.connect(self.discovery_worker.deleteLater)
        self.discovery_thread.finished.connect(self.discovery_thread.deleteLater)

        self.discovery_thread.start()

    def on_discovery_complete(self, arduino_info):
        """
        Callback de la auto-detección (Método 2).
        """
        if arduino_info:
            self.arduino_ip = arduino_info['ip']
            self.statusBar().showMessage(f"¡Arduino encontrado en {self.arduino_ip}! Conectando...")
            self.ip_display.setText(self.arduino_ip)
            self.iniciar_hilo_trabajador()
        else:
            self.statusBar().showMessage("No se encontró el Arduino automáticamente. Por favor, ingrese la IP.")
            self.search_btn.setEnabled(True)  # Re-habilita el botón
            self.search_btn.setText("BUSCAR IP")
            self.solicitar_ip_manualmente()  # Pasa al fallback manual

    def solicitar_ip_manualmente(self):
        """
        Método 3: Fallback manual si la auto-detección falla.
        """
        ip, ok = QInputDialog.getText(self, 'IP del Arduino',
                                      'No se encontró el Arduino.\nPor favor, ingrese la dirección IP:')
        if ok and ip:
            self.arduino_ip = ip
            self.statusBar().showMessage(f"Intentando conectar con {self.arduino_ip}...")
            self.ip_display.setText(self.arduino_ip)
            self.search_btn.setEnabled(False)  # Deshabilita el botón
            self.search_btn.setText("Conectando...")
            self.iniciar_hilo_trabajador()
        else:
            self.statusBar().showMessage("Operación cancelada.")
            self.search_btn.setEnabled(True)  # Re-habilita el botón
            self.search_btn.setText("BUSCAR IP")

    def iniciar_hilo_trabajador(self):
        # (Este método no cambia, solo se reutiliza)
        self.data_thread = QtCore.QThread()
        self.data_worker = ArduinoWorker(arduino_ip=self.arduino_ip)
        self.data_worker.moveToThread(self.data_thread)

        self.data_thread.started.connect(self.data_worker.run)
        self.data_worker.datos_actualizados.connect(self.actualizar_todo)
        self.data_worker.error_ocurrido.connect(self.mostrar_error)
        self.data_worker.finished.connect(self.data_thread.quit)
        self.data_worker.finished.connect(self.data_worker.deleteLater)
        self.data_thread.finished.connect(self.data_thread.deleteLater)

        self.data_thread.start()

    def iniciar_timer_reloj(self):
        # (Sin cambios)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000)
        self.actualizar_reloj()

    # --- (Funciones de actualización de historial sin cambios) ---
    def actualizar_sensor(self, sensor_name, nuevo_valor_str):
        try:
            labels = self.sensor_labels[sensor_name]
            labels[3].setText(labels[2].text())
            labels[2].setText(labels[1].text())
            labels[1].setText(labels[0].text())
            labels[0].setText(nuevo_valor_str)
        except KeyError:
            print(f"Error: No se encontró la clave del sensor '{sensor_name}'")
        except Exception as e:
            print(f"Error al actualizar sensor: {e}")

    def _actualizar_temp(self, temp):
        self.actualizar_sensor('temp', f"{temp:.1f}°C")

    def _actualizar_hum(self, hum):
        self.actualizar_sensor('hum', f"{hum:.1f}%")

    def _actualizar_presion(self, presion):
        self.actualizar_sensor('pres', f"{presion:.1f} mbar")

    def _actualizar_lluv(self, estado_lluvia):
        self.rain_indicator.setState(estado_lluvia)

    def _actualizar_qai(self, qai):
        self.actualizar_sensor('qai', str(qai))

    # --- (Funciones de actualización de gráfico sin cambios) ---
    def actualizar_todo(self, data):
        self._actualizar_temp(data['temperature'])
        self._actualizar_hum(data['humidity'])
        self._actualizar_presion(data['pressure'])
        self._actualizar_qai(data['aqi'])
        self._actualizar_lluv(data['rainfall'])

        self.time_data.append(self.x_counter)
        self.temp_data.append(data['temperature'])
        self.hum_data.append(data['humidity'])
        self.x_counter += 1

        if len(self.time_data) > self.max_points:
            self.time_data.pop(0)
            self.temp_data.pop(0)
            self.hum_data.pop(0)

        self.actualizar_grafica()

    def actualizar_grafica(self):
        self.temp_curve.setData(self.time_data, self.temp_data)
        self.hum_curve.setData(self.time_data, self.hum_data)

    def actualizar_reloj(self):
        now = QtCore.QDateTime.currentDateTime()
        formato_deseado = "dd/MM/yy hh:mm ap"
        self.fecha_hora_display.setText(now.toString(formato_deseado))

    # --- MÉTODO MODIFICADO ---
    def mostrar_error(self, mensaje):
        """Muestra errores en la barra de estado y reactiva el botón"""
        self.statusBar().showMessage(mensaje)

        # Si la conexión falla (por cualquier método),
        # reactivamos el botón para que el usuario pueda
        # intentar el Método 2 (Auto-discovery)
        self.search_btn.setEnabled(True)
        self.search_btn.setText("BUSCAR IP")

    def closeEvent(self, event):
        # (Sin cambios)
        if self.data_thread and self.data_thread.isRunning():
            self.data_worker.stop()
            self.data_thread.quit()
            self.data_thread.wait()
        event.accept()


# --- PARTE 4: PUNTO DE ENTRADA (Sin cambios) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = EstacionApp()
    window.show()
    sys.exit(app.exec_())