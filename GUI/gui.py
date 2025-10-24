# GUI/gui.py
# (Código de "estilo 1" limpio y listo para la lógica)

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QRadioButton)
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt


# --- WIDGET LED ---
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

        # --- Configuración de la Ventana ---
        self.setWindowTitle("Sistema Climático ITQ")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #1a639a; color: white;")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- Creación de Layouts ---
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

        # --- NUEVO: Añadimos la barra de estado ---
        self.statusBar().setStyleSheet("color: white;")

    # --- Creación de Imágenes ---
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
        # Guardamos las ETIQUETAS de datos para poder actualizarlas
        (temp_widget, self.temp_label) = self._create_single_sensor_box("TEMP")
        (hum_widget, self.hum_label) = self._create_single_sensor_box("HUMEDAD")
        (pres_widget, self.pres_label) = self._create_single_sensor_box("PRESION")
        (qai_widget, self.qai_label) = self._create_single_sensor_box("QAI")
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

        # Tus líneas de altura (¡perfectas!)
        content_box.setMaximumHeight(160)
        content_box.setMinimumHeight(140)

        content_box.setStyleSheet("background-color: white; color: black;")

        # --- AQUÍ ESTÁ EL CAMBIO ---

        # 1. Crea el layout
        content_layout = QVBoxLayout()

        # 2. Crea la etiqueta de datos
        data_label = QLabel("---")
        data_font = QFont('Arial', 24, QFont.Bold)
        data_label.setFont(data_font)
        # Nota: setAlignment en la etiqueta solo centra horizontalmente
        data_label.setAlignment(Qt.AlignCenter)
        data_label.setStyleSheet("color: black;")

        # 3. Añade la etiqueta al layout
        content_layout.addWidget(data_label)

        # 4. ¡LA LÍNEA MÁGICA!
        # Esto centra todo el contenido del layout (la data_label)
        # tanto vertical como horizontalmente.
        content_layout.setAlignment(Qt.AlignCenter)

        # --- FIN DEL CAMBIO ---

        content_box.setLayout(content_layout)
        wrapper_layout.addWidget(title_label)
        wrapper_layout.addWidget(content_box)

        return (wrapper_widget, data_label)

    # --- Creación de Leyenda ---
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

    # --- Creación de Gráfica ---
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

    # --- MÉTODO MODIFICADO ---
    def _create_bottom_bar(self):
        layout = QHBoxLayout()
        # Widgets de tu archivo
        self.fecha_hora_display = QLineEdit()
        self.fecha_hora_display.setPlaceholderText("FECHA Y HORA")
        self.fecha_hora_display.setReadOnly(True)
        self.ip_display = QLineEdit()
        self.ip_display.setPlaceholderText("IP DEL ARDUINO")
        self.ip_display.setReadOnly(True)
        self.importar_btn = QPushButton("IMPORTAR")
        self.exit_btn = QPushButton("EXIT")

        # --- NUEVO: Botón de Búsqueda ---
        self.search_btn = QPushButton("BUSCAR IP")

        # Estilos de tu archivo
        style_sheet = """
            QLineEdit { background-color: white; color: black; }
            QPushButton { background-color: #eee; color: black; }
        """
        self.fecha_hora_display.setStyleSheet(style_sheet)
        self.ip_display.setStyleSheet(style_sheet)
        self.importar_btn.setStyleSheet(style_sheet)
        self.exit_btn.setStyleSheet(style_sheet)

        # Aplicamos estilo al nuevo botón
        self.search_btn.setStyleSheet(style_sheet)

        self.exit_btn.clicked.connect(self.close)

        # Layout (modificado para añadir el nuevo botón)
        layout.addWidget(self.fecha_hora_display)
        layout.addWidget(self.ip_display)
        layout.addStretch(1)
        layout.addWidget(self.search_btn)  # Botón añadido
        layout.addWidget(self.importar_btn)
        layout.addWidget(self.exit_btn)
        return layout