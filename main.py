import sys
import time
import requests
import socket
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QApplication, QFileDialog, QMessageBox
from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
from GUI.gui import Ui_MainWindow

from collections import deque
from export_utils import export_data_to_excel


# --- LÓGICA DE DETECCIÓN ---
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


# --- LÓGICA DEL WORKER DE DATOS ---
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


# --- LA APLICACIÓN PRINCIPAL ---
class EstacionApp(Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.KNOWN_IPS = [
            "172.16.42.213",  # 3. TecNorte
            "172.20.0.44",  # 1. TecNM-ITQuerétaro
            "192.168.3.100",  # 2. HUAWEI-C137
        ]
        self.current_ip_index = 0

        self.arduino_ip = None
        self.data_thread = None

        self.is_connected = False
        self.has_connected_once = False
        self.connection_alert_box = None

        # Listas para el gráfico
        self.max_graph_points = 50
        self.time_data = []
        self.temp_data = []
        self.hum_data = []
        self.x_counter = 0

        # Listas para historial de exportación
        self.max_history_points = 500
        self.temp_history = deque(maxlen=self.max_history_points)
        self.hum_history = deque(maxlen=self.max_history_points)
        self.pres_history = deque(maxlen=self.max_history_points)
        self.qai_history = deque(maxlen=self.max_history_points)

        self.iniciar_timer_reloj()

        self.search_btn.clicked.connect(self.iniciar_busqueda_arduino)
        self.importar_btn.clicked.connect(self.exportar_a_excel)

        self.iniciar_conexion_secuencial()

    def stop_current_worker(self):
        """Función de ayuda para detener cualquier hilo de datos activo."""
        if self.data_thread and self.data_thread.isRunning():
            self.data_worker.stop()
            self.data_thread.quit()
            self.data_thread.wait()

    def iniciar_conexion_secuencial(self):
        """
        Intenta conectarse a la IP actual en la lista self.KNOWN_IPS.
        """
        if self.current_ip_index >= len(self.KNOWN_IPS):
            self.statusBar().showMessage("Conexión automática fallida. Use 'BUSCAR IP'.")
            self.search_btn.setEnabled(True)
            self.search_btn.setText("BUSCAR IP")
            return

        ip_to_try = self.KNOWN_IPS[self.current_ip_index]

        self.statusBar().showMessage(f"Intentando conexión automática a {ip_to_try}...")
        self.arduino_ip = ip_to_try
        self.ip_display.setText(self.arduino_ip)
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Conectando...")

        self.iniciar_hilo_trabajador()

    def iniciar_busqueda_arduino(self):
        """Método 2: Detiene cualquier intento y usa Zeroconf."""
        self.stop_current_worker()

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
        """Método 3: Fallback manual."""
        self.stop_current_worker()

        ip, ok = QInputDialog.getText(self, 'IP del Arduino',
                                      'No se encontró el Arduino.\nPor favor, ingrese la dirección IP:')
        if ok and ip:
            self.arduino_ip = ip
            self.statusBar().showMessage(f"Intentando conectar con {self.arduino_ip}...")
            self.ip_display.setText(self.arduino_ip)
            self.search_btn.setEnabled(False)
            self.search_btn.setText("Conectado")
            self.iniciar_hilo_trabajador()
        else:
            self.statusBar().showMessage("Operación cancelada.")
            self.search_btn.setEnabled(True)
            self.search_btn.setText("BUSCAR IP")

    def iniciar_hilo_trabajador(self):
        self.is_connected = False
        if self.connection_alert_box:
            self.connection_alert_box.accept()
            self.connection_alert_box = None

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
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000)
        self.actualizar_reloj()

    def actualizar_sensor(self, sensor_name, nuevo_valor_str):
        try:
            labels = self.sensor_labels[sensor_name]
            labels[3].setText(labels[2].text())
            labels[2].setText(labels[1].text())
            labels[1].setText(labels[0].text())
            labels[0].setText(nuevo_valor_str)
        except KeyError:
            print(f"Error: No se encontró la clave del sensor '{sensor_name}'")

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

    def actualizar_todo(self, data):
        if not self.is_connected:
            self.is_connected = True
            self.statusBar().showMessage(f"¡Conexión establecida con {self.arduino_ip}!")

            self.search_btn.setEnabled(False)
            self.search_btn.setText("Conectado")

            if self.connection_alert_box:
                self.connection_alert_box.accept()
                self.connection_alert_box = None

            if self.has_connected_once:
                QMessageBox.information(self,
                                        "Conexión Recuperada",
                                        f"Se ha reconectado exitosamente al Modulo en {self.arduino_ip}.")
            else:
                self.has_connected_once = True

        self._actualizar_temp(data['temperature'])
        self._actualizar_hum(data['humidity'])
        self._actualizar_presion(data['pressure'])
        self._actualizar_qai(data['aqi'])
        self._actualizar_lluv(data['rainfall'])

        self.time_data.append(self.x_counter)
        self.temp_data.append(data['temperature'])
        self.hum_data.append(data['humidity'])
        self.x_counter += 1

        if len(self.time_data) > self.max_graph_points:
            self.time_data.pop(0)
            self.temp_data.pop(0)
            self.hum_data.pop(0)

        self.temp_history.append(data['temperature'])
        self.hum_history.append(data['humidity'])
        self.pres_history.append(data['pressure'])
        self.qai_history.append(data['aqi'])

        self.actualizar_grafica()

    def actualizar_grafica(self):
        self.temp_curve.setData(self.time_data, self.temp_data)
        self.hum_curve.setData(self.time_data, self.hum_data)

    def actualizar_reloj(self):
        now = QtCore.QDateTime.currentDateTime()
        formato_deseado = "dd/MM/yy hh:mm ap"
        self.fecha_hora_display.setText(now.toString(formato_deseado))

    # --- LÓGICA DE ERROR MODIFICADA ---
    def mostrar_error(self, mensaje):
        self.statusBar().showMessage(f"{mensaje}. Reintentando...")

        # Si el error ocurre DURANTE la secuencia automática inicial...
        if not self.has_connected_once:
            print(f"Intento fallido para {self.arduino_ip}. Probando siguiente IP.")

            # Detenemos el worker actual ANTES de iniciar el siguiente.
            self.stop_current_worker()

            self.current_ip_index += 1  # Pasamos a la siguiente IP
            self.iniciar_conexion_secuencial()  # Intentamos de nuevo
            return  # No mostramos pop-up ni habilitamos el botón

        # Si el error ocurre DESPUÉS de una conexión exitosa...
        self.search_btn.setEnabled(True)
        self.search_btn.setText("BUSCAR IP")

        if self.is_connected and self.has_connected_once:
            self.is_connected = False
            print(f"¡Conexión perdida! Error: {mensaje}")
            self.connection_alert_box = QMessageBox(self)
            self.connection_alert_box.setIcon(QMessageBox.Warning)
            self.connection_alert_box.setWindowTitle("Conexión Perdida")
            self.connection_alert_box.setText(f"Se perdió la conexión con el Modulo.\n {mensaje}\n\n"
                                              "Los datos se están guardando en la SD del Modulo.\n"
                                              "La aplicación intentará reconectarse automáticamente.")
            self.connection_alert_box.setStandardButtons(QMessageBox.Ok)
            self.connection_alert_box.show()
        else:
            self.is_connected = False

    def closeEvent(self, event):
        self.stop_current_worker()
        event.accept()

    def exportar_a_excel(self):
        export_data_to_excel(
            parent_window=self,
            status_bar=self.statusBar(),
            temp_history=self.temp_history,
            hum_history=self.hum_history,
            pres_history=self.pres_history,
            qai_history=self.qai_history
        )


# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = EstacionApp()
    window.show()
    sys.exit(app.exec_())