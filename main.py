
import sys
import time
import requests
from PyQt5 import QtCore, QtGui, QtWidgets



# --- 2. EL HILO TRABAJADOR (LÓGICA EN SEGUNDO PLANO) -------------
class ArduinoWorker(QtCore.QObject):
    temperatura_actualizada = QtCore.pyqtSignal(float)
    humedad_actualizada = QtCore.pyqtSignal(float)
    # NOTA: Arduino envía "pressure", lo mapearemos a tu widget "viento".
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

            except requests.exceptions.RequestException as e:
                self.error_ocurrido.emit(f"Error de conexión")
                time.sleep(5)
            except KeyError as e:
                self.error_ocurrido.emit(f"Dato no encontrado: {e}")

            time.sleep(1)
        self.finished.emit()

    def stop(self):
        self.is_running = False


# -------------------------------------------------------------------
# --- 3. TU CLASE DE LA INTERFAZ GRÁFICA (DISEÑO) -----------------
# --- (Copiada y pegada, sin modificaciones) ----------------------
# -------------------------------------------------------------------
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1119, 765)
        MainWindow.setAutoFillBackground(False)
        MainWindow.setStyleSheet("background-color: #d2f4f9;")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.vault_temp = QtWidgets.QLineEdit(self.centralwidget)
        self.vault_temp.setGeometry(QtCore.QRect(30, 160, 171, 151))
        self.vault_temp.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.vault_temp.setObjectName("vault_temp")
        self.vault_lluv = QtWidgets.QLineEdit(self.centralwidget)
        self.vault_lluv.setGeometry(QtCore.QRect(690, 160, 171, 151))
        self.vault_lluv.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.vault_lluv.setObjectName("vault_lluv")
        self.vault_hum = QtWidgets.QLineEdit(self.centralwidget)
        self.vault_hum.setGeometry(QtCore.QRect(260, 160, 171, 151))
        self.vault_hum.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.vault_hum.setObjectName("vault_hum")
        self.vault_vien = QtWidgets.QLineEdit(self.centralwidget)
        self.vault_vien.setGeometry(QtCore.QRect(480, 160, 171, 151))
        self.vault_vien.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.vault_vien.setObjectName("vault_vien")
        self.graphics_View = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphics_View.setGeometry(QtCore.QRect(30, 340, 1051, 321))
        self.graphics_View.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.graphics_View.setObjectName("graphics_View")
        self.button_stop = QtWidgets.QPushButton(self.centralwidget)
        self.button_stop.setGeometry(QtCore.QRect(1010, 700, 75, 23))
        self.button_stop.setStyleSheet("background-color: #ffffff;")
        self.button_stop.setObjectName("button_stop")
        self.button_expo = QtWidgets.QPushButton(self.centralwidget)
        self.button_expo.setGeometry(QtCore.QRect(910, 700, 75, 23))
        self.button_expo.setStyleSheet("background-color: #ffffff;")
        self.button_expo.setObjectName("button_expo")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(60, 10, 71, 61))
        self.label.setText("")
        # --- Nota: Las rutas de las imágenes deben ser correctas o la app dará error ---
        # self.label.setPixmap(QtGui.QPixmap("../../../Pictures/ITQ Herramientas/LOGOS-INSTITUCIONALES-ITQ-04.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(530, 20, 71, 61))
        self.label_2.setText("")
        # self.label_2.setPixmap(QtGui.QPixmap("../../../Pictures/ITQ Herramientas/20181011001342_44_mascotOrig.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(830, 20, 241, 61))
        self.label_3.setText("")
        # self.label_3.setPixmap(QtGui.QPixmap("../../../Pictures/ITQ Herramientas/Logo-TecNM.png"))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.vault_fecha_hora = QtWidgets.QLabel(self.centralwidget)
        self.vault_fecha_hora.setGeometry(QtCore.QRect(30, 670, 221, 31))
        self.vault_fecha_hora.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.vault_fecha_hora.setObjectName("vault_fecha_hora")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(60, 120, 111, 31))
        self.label_5.setStyleSheet("font-size: 16px; font-weight: bold; color: #0b0b0b; font: 75 12pt")
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(310, 120, 81, 31))
        self.label_6.setStyleSheet("font-size: 16px; font-weight: bold; color: #0b0b0b; font: 75 12pt")
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(540, 120, 61, 31))
        self.label_7.setStyleSheet("font-size: 16px; font-weight: bold; color: #0b0b0b; font: 75 12pt")
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.centralwidget)
        self.label_8.setGeometry(QtCore.QRect(750, 120, 61, 31))
        self.label_8.setStyleSheet("font-size: 16px; font-weight: bold; color: #0b0b0b; font: 75 12pt")
        self.label_8.setObjectName("label_8")
        self.vault_qai = QtWidgets.QLineEdit(self.centralwidget)
        self.vault_qai.setGeometry(QtCore.QRect(910, 160, 171, 151))
        self.vault_qai.setStyleSheet(
            "background-color: #ffffff;\nborder: 1px solid #000000;\nborder-radius: 5px;\npadding: 5px;")
        self.vault_qai.setObjectName("vault_qai")
        self.label_9 = QtWidgets.QLabel(self.centralwidget)
        self.label_9.setGeometry(QtCore.QRect(980, 120, 31, 31))
        self.label_9.setStyleSheet("font-size: 16px; font-weight: bold; color: #0b0b0b; font: 75 12pt")
        self.label_9.setObjectName("label_9")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1119, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Estación Meteorologica"))
        self.button_stop.setText(_translate("MainWindow", "STOP"))
        self.button_expo.setText(_translate("MainWindow", "EXPORTAR"))
        self.vault_fecha_hora.setText(_translate("MainWindow", "FECHA_HORA"))
        self.label_5.setText(_translate("MainWindow", "TEMPERATURA"))
        self.label_6.setText(_translate("MainWindow", "HUMEDAD"))
        self.label_7.setText(_translate("MainWindow", "VIENTO"))
        self.label_8.setText(_translate("MainWindow", "LLUVIA"))
        self.label_9.setText(_translate("MainWindow", "QAI"))


# --- 4. LA CLASE PRINCIPAL DE LA APLICACIÓN (EL CEREBRO) ---------
class EstacionApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Cargar tu diseño
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 2. Configurar mejoras en la UI
        self.configurar_ui_adicional()

        # 3. Iniciar el hilo que obtiene los datos del Arduino
        self.iniciar_hilo_trabajador()

        # 4. Iniciar un temporizador para la fecha y hora
        self.iniciar_timer_reloj()

    def configurar_ui_adicional(self):
        """Ajustes para que los QLineEdit se vean mejor como displays."""
        font = QtGui.QFont('Arial', 24, QtGui.QFont.Bold)
        widgets_a_configurar = [
            self.ui.vault_temp, self.ui.vault_hum, self.ui.vault_vien,
            self.ui.vault_lluv, self.ui.vault_qai
        ]
        for widget in widgets_a_configurar:
            widget.setFont(font)
            widget.setReadOnly(True)  # Para que no se puedan editar
            widget.setAlignment(QtCore.Qt.AlignCenter)  # Centrar el texto

        # Conectar el botón STOP a la función de cerrar la ventana
        self.ui.button_stop.clicked.connect(self.close)

    def iniciar_hilo_trabajador(self):
        """Crea, configura y arranca el hilo y el trabajador."""
        self.thread = QtCore.QThread()
        # ❗ IMPORTANTE: Reemplaza con la IP real de tu Arduino
        arduino_ip = "172.16.49.253"
        self.worker = ArduinoWorker(arduino_ip=arduino_ip)
        self.worker.moveToThread(self.thread)

        # Conectar señales del worker a los slots (métodos) de esta clase
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.temperatura_actualizada.connect(self.actualizar_temp)
        self.worker.humedad_actualizada.connect(self.actualizar_hum)
        self.worker.presion_actualizada.connect(self.actualizar_vien)  # Mapeamos presión a viento
        self.worker.lluvia_actualizada.connect(self.actualizar_lluv)
        self.worker.aqi_actualizado.connect(self.actualizar_qai)
        self.worker.error_ocurrido.connect(self.mostrar_error)

        self.thread.start()

    def iniciar_timer_reloj(self):
        """Crea un QTimer que actualiza la fecha y hora cada segundo."""
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.actualizar_reloj)
        self.timer.start(1000)  # Se activa cada 1000 ms (1 segundo)
        self.actualizar_reloj()  # Llamada inicial para que no empiece vacío

    # --- SLOTS (MÉTODOS) QUE ACTUALIZAN TU INTERFAZ ---

    def actualizar_temp(self, temp):
        self.ui.vault_temp.setText(f"{temp:.1f}°C")

    def actualizar_hum(self, hum):
        self.ui.vault_hum.setText(f"{hum:.1f}%")

    def actualizar_vien(self, presion):
        # Nota: Estamos mostrando el valor de la presión en el campo de viento.
        self.ui.vault_vien.setText(f"{presion:.1f} mbar")

    def actualizar_lluv(self, estado_lluvia):
        texto = "Sí" if estado_lluvia == 1 else "No"
        self.ui.vault_lluv.setText(texto)

    def actualizar_qai(self, qai):
        self.ui.vault_qai.setText(str(qai))

    def actualizar_reloj(self):
        now = QtCore.QDateTime.currentDateTime()
        self.ui.vault_fecha_hora.setText(now.toString("dd-MM-yyyy hh:mm:ss ap"))

    def mostrar_error(self, mensaje):
        self.ui.statusbar.showMessage(f"Error: {mensaje}", 5000)  # Muestra en la barra de estado por 5 seg
        print(f"ERROR: {mensaje}")

    def closeEvent(self, event):
        """Se asegura de detener el hilo cuando se cierra la ventana."""
        if self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()  # Espera a que el hilo termine limpiamente
        event.accept()


# -------------------------------------------------------------------
# --- 5. PUNTO DE ENTRADA DE LA APLICACIÓN ------------------------
# -------------------------------------------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # Creamos una instancia de nuestra clase principal, no de la Ui_MainWindow
    window = EstacionApp()
    window.show()
    sys.exit(app.exec_())