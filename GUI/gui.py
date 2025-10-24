# GUI/gui.py
# (Modificado para historial de 4 etiquetas)

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QRadioButton)
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt


# --- WIDGET LED (Sin cambios) ---
class LedRadioButton(QRadioButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("")
        self.setCheckable(False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._is_on = False
        self._update_style()

    def _update_style(self):
        color = "lime" if self._is_on else "red"
        style = f"""
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                background-color: {color};
            }}
        """
        self.setStyleSheet(style)

    def setState(self, is_on):
        state = bool(is_on)
        if self._is_on != state:
            self._is_on = state
            self._update_style()


# --- CLASE PRINCIPAL DE LA VENTANA ---
class Ui_MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- NUEVO: Diccionario para guardar las etiquetas ---
        self.sensor_labels = {}

        self.setWindowTitle("Sistema Climático ITQ")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #1a639a; color: white;")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.main_layout = QVBoxLayout(self.central_widget)

        image_bar_layout = self._create_image_bar()
        self.main_layout.addLayout(image_bar_layout)
        sensor_boxes_layout = self._create_sensor_boxes()
        self.main_layout.addLayout(sensor_boxes_layout)
        legend_layout = self._create_legend()
        self.main_layout.addLayout(legend_layout)
        graph_groupbox = self._create_graph_area()
        self.main_layout.addWidget(graph_groupbox)
        bottom_bar_layout = self._create_bottom_bar()
        self.main_layout.addLayout(bottom_bar_layout)

        self.statusBar().setStyleSheet("color: white;")

    def _create_image_placeholder(self, image_path):
        label = QLabel()
        label.setMinimumSize(120, 80)
        label.setMaximumSize(150, 80)
        label.setAlignment(Qt.AlignCenter)
        if not os.path.exists(image_path):
            print(f"Advertencia: No se pudo encontrar la imagen en {image_path}")
            label.setText("IMG NO\nENCONTRADA")
            label.setStyleSheet("color: yellow; border: 1px dashed yellow;")
            return label
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        return label

    def _create_image_bar(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        ruta_img_izquierda = "images/LOGO_ITQ_TECNM_BLANCO.png"
        ruta_img_centro = "images/20181011001342_44_mascotOrig.png"
        ruta_img_derecha = "images/LOGOS-INSTITUCIONALES-ITQ-04.png"
        img_left = self._create_image_placeholder(ruta_img_izquierda)
        img_center = self._create_image_placeholder(ruta_img_centro)
        img_right = self._create_image_placeholder(ruta_img_derecha)
        layout.addWidget(img_left)
        layout.addStretch(1)
        layout.addWidget(img_center)
        layout.addStretch(1)
        layout.addWidget(img_right)
        return layout

    # --- MÉTODO MODIFICADO ---
    def _create_sensor_boxes(self):
        layout = QHBoxLayout()
        # Ahora almacenamos las 4 etiquetas de cada sensor en el diccionario
        (temp_widget, self.sensor_labels['temp']) = self._create_single_sensor_box("TEMP")
        (hum_widget, self.sensor_labels['hum']) = self._create_single_sensor_box("HUMEDAD")
        (pres_widget, self.sensor_labels['pres']) = self._create_single_sensor_box("PRESION")
        (qai_widget, self.sensor_labels['qai']) = self._create_single_sensor_box("QAI")

        layout.addWidget(temp_widget)
        layout.addWidget(hum_widget)
        layout.addWidget(pres_widget)
        layout.addWidget(qai_widget)
        return layout

    # --- MÉTODO MODIFICADO ---
    def _create_single_sensor_box(self, title):
        wrapper_widget = QWidget()
        wrapper_layout = QVBoxLayout(wrapper_widget)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)

        content_box = QGroupBox("")
        content_box.setMaximumHeight(160)  # Mantenemos tu ajuste de altura
        content_box.setMinimumHeight(140)
        content_box.setStyleSheet("background-color: white; color: black;")

        content_layout = QVBoxLayout()

        # --- NUEVO: Creamos las 4 etiquetas de historial ---

        # Fuente para el historial (pos 2, 3, 4)
        history_font = QFont('Arial', 18)

        # Fuente para la lectura en vivo (pos 1)
        live_font = QFont('Arial', 29, QFont.Bold)

        # Posición 4 (Arriba)
        label_pos4 = QLabel("")  # Inicia vacío
        label_pos4.setFont(history_font)
        label_pos4.setAlignment(Qt.AlignCenter)

        # Posición 3
        label_pos3 = QLabel("")  # Inicia vacío
        label_pos3.setFont(history_font)
        label_pos3.setAlignment(Qt.AlignCenter)

        # Posición 2
        label_pos2 = QLabel("")  # Inicia vacío
        label_pos2.setFont(history_font)
        label_pos2.setAlignment(Qt.AlignCenter)

        # Posición 1 (Abajo, en vivo)
        label_pos1 = QLabel("---")  # Texto inicial
        label_pos1.setFont(live_font)
        label_pos1.setAlignment(Qt.AlignCenter)

        # Añadimos las etiquetas al layout en orden (de arriba a abajo)
        content_layout.addWidget(label_pos4)
        content_layout.addWidget(label_pos3)
        content_layout.addWidget(label_pos2)
        content_layout.addWidget(label_pos1)

        # --- FIN DE LA MODIFICACIÓN ---

        content_box.setLayout(content_layout)
        wrapper_layout.addWidget(title_label)
        wrapper_layout.addWidget(content_box)

        # Devolvemos el widget Y la LISTA de etiquetas
        # [0]=vivo, [1]=hist1, [2]=hist2, [3]=hist3
        labels_list = [label_pos1, label_pos2, label_pos3, label_pos4]

        return (wrapper_widget, labels_list)

    def _create_legend(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.rain_indicator = LedRadioButton()
        self.rain_indicator.setState(False)
        hum_indicator = QFrame()
        hum_indicator.setFixedSize(30, 15)
        hum_indicator.setStyleSheet("background-color: blue;")
        temp_indicator = QFrame()
        temp_indicator.setFixedSize(30, 15)
        temp_indicator.setStyleSheet("background-color: red;")
        layout.addWidget(self.rain_indicator)
        layout.addWidget(QLabel("LLUVIA"))
        layout.addSpacing(20)
        layout.addWidget(hum_indicator)
        layout.addWidget(QLabel("HUMEDAD"))
        layout.addSpacing(20)
        layout.addWidget(temp_indicator)
        layout.addWidget(QLabel("TEMP"))
        layout.addStretch(1)
        return layout

    def _create_graph_area(self):
        graph_box = QGroupBox("GRAFICA TEMP Y HUMEDAD")
        graph_box.setStyleSheet("background-color: white; color: black;")
        graph_layout = QVBoxLayout()
        placeholder_label = QLabel("AQUÍ VA LA GRÁFICA")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("background-color: #eee; border: 1px solid #ccc; color: black;")
        graph_layout.addWidget(placeholder_label)
        graph_box.setLayout(graph_layout)
        graph_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        return graph_box

    def _create_bottom_bar(self):
        layout = QHBoxLayout()
        self.fecha_hora_display = QLineEdit()
        self.fecha_hora_display.setPlaceholderText("FECHA Y HORA")
        self.fecha_hora_display.setReadOnly(True)
        self.ip_display = QLineEdit()
        self.ip_display.setPlaceholderText("IP DEL ARDUINO")
        self.ip_display.setReadOnly(True)
        self.importar_btn = QPushButton("IMPORTAR")
        self.exit_btn = QPushButton("EXIT")
        self.search_btn = QPushButton("BUSCAR IP")

        style_sheet = """
            QLineEdit { background-color: white; color: black; }
            QPushButton { background-color: #eee; color: black; }
        """
        self.fecha_hora_display.setStyleSheet(style_sheet)
        self.ip_display.setStyleSheet(style_sheet)
        self.importar_btn.setStyleSheet(style_sheet)
        self.exit_btn.setStyleSheet(style_sheet)
        self.search_btn.setStyleSheet(style_sheet)

        self.exit_btn.clicked.connect(self.close)

        layout.addWidget(self.fecha_hora_display)
        layout.addWidget(self.ip_display)
        layout.addStretch(1)
        layout.addWidget(self.search_btn)
        layout.addWidget(self.importar_btn)
        layout.addWidget(self.exit_btn)
        return layout