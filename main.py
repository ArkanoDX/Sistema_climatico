# main.py
import sys
import time
import requests
import socket
# NUEVO: Importamos el QInputDialog para pedir la IP
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog

from zeroconf import ServiceBrowser, Zeroconf, ServiceListener

# Importamos la clase del diseño desde tu archivo gui.py
from GUI.gui import Ui_MainWindow


# --- CLASES PARA DESCUBRIR EL ARDUINO EN LA RED (Sin cambios) ---
class ArduinoListener(ServiceListener):
    def __init__(self):
        self.arduino_info = None

    def add_service(self, zc, type_, name):
        if "sistemaclima-tecnm" in name:
            info = zc.get_service_info(type_, name)
            if info:
                ip_address = socket.inet_ntoa(info.addresses[0])
                self.arduino_info = {"ip": ip_address}

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


# --- EL HILO TRABAJADOR QUE OBTIENE DATOS (Sin cambios) ---
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
                data = response.json()
                self.temperatura_actualizada.emit(data['temperature'])
                self.humedad_actualizada.emit(data['humidity'])
                self.presion_actualizada.emit(data['pressure'])
                self.aqi_actualizado.emit(data['aqi'])
                self.lluvia_actualizada.emit(data['rainfall'])
            except Exception as e:
                self.error_ocurrido.emit("Error de conexión con el Arduino")
                time.sleep(5)
            time.sleep(1)
        self.finished.emit()

    def stop(self):
        self.is_running = False


# --- LA CLASE PRINCIPAL DE LA APLICACIÓN (EL CEREBRO) ---------
class EstacionApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.arduino_ip = None
        self.data_thread = None
        self.configurar_ui_adicional()
        self.iniciar_timer_reloj()
        self.iniciar_busqueda_arduino()

    def configurar_ui_adicional(self):
        font = QtGui.QFont('Arial', 24, QtGui.QFont.Bold)
        widgets = [self.ui.vault_temp, self.ui.vault_hum, self.ui.vault_vien, self.ui.vault_lluv, self.ui.vault_qai]
        for widget in widgets:
            widget.setFont(font)
            widget.setReadOnly(True)
            widget.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.button_stop.clicked.connect(self.close)

    def iniciar_busqueda_arduino(self):
        self.ui.statusbar.showMessage("Buscando Arduino en la red...")
        self.discovery_thread = QtCore.QThread()
        self.discovery_worker = DiscoveryWorker()
        self.discovery_worker.moveToThread(self.discovery_thread)
        self.discovery_thread.started.connect(self.discovery_worker.run)
        self.discovery_worker.found.connect(self.on_discovery_complete)
        self.discovery_worker.finished.connect(self.discovery_thread.quit)
        self.discovery_worker.finished.connect(self.discovery_worker.deleteLater)
        self.discovery_thread.finished.connect(self.discovery_thread.deleteLater)
        self.discovery_thread.start()

    # --- MÉTODO MODIFICADO PARA INCLUIR EL FALLBACK ---
    def on_discovery_complete(self, arduino_info):
        if arduino_info:
            self.arduino_ip = arduino_info['ip']
            self.ui.statusbar.showMessage(f"¡Arduino encontrado en {self.arduino_ip}! Conectando...")
            self.iniciar_hilo_trabajador()
        else:
            self.ui.statusbar.showMessage("No se encontró el Arduino automáticamente. Por favor, ingrese la IP.")
            # Si la búsqueda automática falla, llamamos al nuevo método manual
            self.solicitar_ip_manualmente()

    # --- NUEVO MÉTODO PARA PEDIR LA IP MANUALMENTE ---
    def solicitar_ip_manualmente(self):
        # Abre una pequeña ventana de diálogo para que el usuario escriba la IP
        ip, ok = QInputDialog.getText(self, 'IP del Arduino',
                                      'No se encontró el Arduino.\nPor favor, ingrese la dirección IP:')

        # Si el usuario escribió algo y le dio "OK"
        if ok and ip:
            self.arduino_ip = ip
            self.ui.statusbar.showMessage(f"Intentando conectar con {self.arduino_ip}...")
            self.iniciar_hilo_trabajador()
        else:
            self.ui.statusbar.showMessage("Operación cancelada. No se puede conectar sin IP.")

    def iniciar_hilo_trabajador(self):
        self.data_thread = QtCore.QThread()
        self.data_worker = ArduinoWorker(arduino_ip=self.arduino_ip)
        self.data_worker.moveToThread(self.data_thread)
        self.data_thread.started.connect(self.data_worker.run)
        self.data_worker.temperatura_actualizada.connect(self.actualizar_temp)
        self.data_worker.humedad_actualizada.connect(self.actualizar_hum)
        self.data_worker.presion_actualizada.connect(self.actualizar_vien)
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

    def actualizar_temp(self, temp):
        self.ui.vault_temp.setText(f"{temp:.1f}°C")

    def actualizar_hum(self, hum):
        self.ui.vault_hum.setText(f"{hum:.1f}%")

    def actualizar_vien(self, presion):
        self.ui.vault_vien.setText(f"{presion:.1f} mbar")

    def actualizar_lluv(self, estado_lluvia):
        self.ui.vault_lluv.setText("Sí" if estado_lluvia == 1 else "No")

    def actualizar_qai(self, qai):
        self.ui.vault_qai.setText(str(qai))

    def actualizar_reloj(self):
        now = QtCore.QDateTime.currentDateTime()
        self.ui.vault_fecha_hora.setText(now.toString("dd-MM-yyyy hh:mm:ss ap"))

    def mostrar_error(self, mensaje):
        self.ui.statusbar.showMessage(mensaje)

    def closeEvent(self, event):
        if self.data_thread and self.data_thread.isRunning():
            self.data_worker.stop()
            self.data_thread.quit()
            self.data_thread.wait()
        event.accept()


# --- PUNTO DE ENTRADA DE LA APLICACIÓN ---
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = EstacionApp()
    window.show()
    sys.exit(app.exec_())