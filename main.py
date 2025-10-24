# main.py
# (Modificado para lógica de historial)

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
    temperatura_actualizada = QtCore.pyqtSignal(float)
    humedad_actualizada = QtCore.pyqtSignal(float)
    presion_actualizada = QtCore.pyqtSignal(float)
    aqi_actualizado = QtCore.pyqtSignal(int)
    lluvia_actualizada = QtCore.pyqtSignal(int)
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
                self.temperatura_actualizada.emit(data['temperature'])
                self.humedad_actualizada.emit(data['humidity'])
                self.presion_actualizada.emit(data['pressure'])
                self.aqi_actualizado.emit(data['aqi'])
                self.lluvia_actualizada.emit(data['rainfall'])
                # El time.sleep(1) coincide con tu petición de 1 segundo
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

        self.arduino_ip = None
        self.data_thread = None

        self.iniciar_timer_reloj()

        self.search_btn.clicked.connect(self.iniciar_busqueda_arduino)
        self.statusBar().showMessage("Listo. Presione 'BUSCAR IP' para conectar.")

    def iniciar_busqueda_arduino(self):
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
        if arduino_info:
            self.arduino_ip = arduino_info['ip']
            self.statusBar().showMessage(f"¡Arduino encontrado en {self.arduino_ip}! Conectando...")
            self.ip_display.setText(self.arduino_ip)
            self.iniciar_hilo_trabajador()
        else:
            self.statusBar().showMessage("No se encontró el Arduino automáticamente. Por favor, ingrese la IP.")
            self.search_btn.setEnabled(True)
            self.search_btn.setText("BUSCAR IP")
            self.solicitar_ip_manualmente()

    def solicitar_ip_manualmente(self):
        ip, ok = QInputDialog.getText(self, 'IP del Arduino',
                                      'No se encontró el Arduino.\nPor favor, ingrese la dirección IP:')
        if ok and ip:
            self.arduino_ip = ip
            self.statusBar().showMessage(f"Intentando conectar con {self.arduino_ip}...")
            self.ip_display.setText(self.arduino_ip)
            self.iniciar_hilo_trabajador()
        else:
            self.statusBar().showMessage("Operación cancelada.")
            self.search_btn.setEnabled(True)
            self.search_btn.setText("BUSCAR IP")

    def iniciar_hilo_trabajador(self):
        self.data_thread = QtCore.QThread()
        self.data_worker = ArduinoWorker(arduino_ip=self.arduino_ip)
        self.data_worker.moveToThread(self.data_thread)

        self.data_thread.started.connect(self.data_worker.run)
        self.data_worker.temperatura_actualizada.connect(self.actualizar_temp)
        self.data_worker.humedad_actualizada.connect(self.actualizar_hum)
        self.data_worker.presion_actualizada.connect(self.actualizar_presion)
        self.data_worker.lluvia_actualizada.connect(self.actualizar_lluv)
        self.data_worker.aqi_actualizado.connect(self.actualizar_qai)
        self.data_worker.error_ocurrido.connect(self.mostrar_error)

        self.data_worker.finished.connect(self.data_thread.quit)
        self.data_worker.finished.connect(self.data_worker.deleteLater)
        self.data_thread.finished.connect(self.data_thread.deleteLater)

        self.data_thread.start()

    def iniciar_timer_reloj(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000)
        self.actualizar_reloj()

    # --- NUEVO: Función de lógica de historial ---
    def actualizar_sensor(self, sensor_name, nuevo_valor_str):
        """
        Mueve los textos de las etiquetas hacia arriba y
        establece el nuevo valor en la posición 1 (en vivo).
        """
        try:
            # Obtiene la lista de [pos1, pos2, pos3, pos4] para este sensor
            labels = self.sensor_labels[sensor_name]

            # Mueve pos3 -> pos4
            labels[3].setText(labels[2].text())
            # Mueve pos2 -> pos3
            labels[2].setText(labels[1].text())
            # Mueve pos1 -> pos2
            labels[1].setText(labels[0].text())
            # Establece el nuevo valor en pos1 (en vivo)
            labels[0].setText(nuevo_valor_str)

        except KeyError:
            print(f"Error: No se encontró la clave del sensor '{sensor_name}'")
        except Exception as e:
            print(f"Error al actualizar sensor: {e}")

    # --- SLOTS DE ACTUALIZACIÓN (MODIFICADOS) ---
    # Ahora llaman a la nueva función 'actualizar_sensor'

    def actualizar_temp(self, temp):
        self.actualizar_sensor('temp', f"{temp:.1f}°C")

    def actualizar_hum(self, hum):
        self.actualizar_sensor('hum', f"{hum:.1f}%")

    def actualizar_presion(self, presion):
        self.actualizar_sensor('pres', f"{presion:.1f} mbar")

    def actualizar_lluv(self, estado_lluvia):
        # El LED se sigue actualizando por separado
        self.rain_indicator.setState(estado_lluvia)

    def actualizar_qai(self, qai):
        self.actualizar_sensor('qai', str(qai))

    def actualizar_reloj(self):
        now = QtCore.QDateTime.currentDateTime()
        formato_deseado = "dd/MM/yy - hh:mm ap"
        self.fecha_hora_display.setText(now.toString(formato_deseado))

    def mostrar_error(self, mensaje):
        self.statusBar().showMessage(mensaje)

    def closeEvent(self, event):
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