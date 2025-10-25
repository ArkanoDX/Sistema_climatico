# GUI/gui.py
# (Modificado para incluir un PlotWidget de PyQtGraph)

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy,
    QRadioButton)
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt
import pyqtgraph as pg  # <-- 1. Importar PyQtGraph

# Configuración global para que los gráficos tengan fondo blanco
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


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
        graph_groupbox = self._create_graph_area()  # <-- 2. Llamamos al método modificado
        self.main_layout.addWidget(graph_groupbox)
        bottom_bar_layout = self._create_bottom_bar()
        self.main_layout.addLayout(bottom_bar_layout)

        self.statusBar().setStyleSheet("color: white;")

    # --- (Métodos _create_image... y _create_sensor... sin cambios) ---

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

    def _create_sensor_boxes(self):
        layout = QHBoxLayout()
        (temp_widget, self.sensor_labels['temp']) = self._create_single_sensor_box("TEMP")
        (hum_widget, self.sensor_labels['hum']) = self._create_single_sensor_box("HUMEDAD")
        (pres_widget, self.sensor_labels['pres']) = self._create_single_sensor_box("PRESIÓN")
        (qai_widget, self.sensor_labels['qai']) = self._create_single_sensor_box("QAI")
        layout.addWidget(temp_widget)
        layout.addWidget(hum_widget)
        layout.addWidget(pres_widget)
        layout.addWidget(qai_widget)
        return layout

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
        content_box.setMaximumHeight(160)
        content_box.setMinimumHeight(140)
        content_box.setStyleSheet("background-color: white; color: black;")

        content_layout = QVBoxLayout()

        history_font = QFont('Arial', 18)
        live_font = QFont('Arial', 24, QFont.Bold)

        label_pos4 = QLabel("")
        label_pos4.setFont(history_font)
        label_pos4.setAlignment(Qt.AlignCenter)

        label_pos3 = QLabel("")
        label_pos3.setFont(history_font)
        label_pos3.setAlignment(Qt.AlignCenter)

        label_pos2 = QLabel("")
        label_pos2.setFont(history_font)
        label_pos2.setAlignment(Qt.AlignCenter)

        label_pos1 = QLabel("---")
        label_pos1.setFont(live_font)
        label_pos1.setAlignment(Qt.AlignCenter)

        content_layout.addWidget(label_pos4)
        content_layout.addWidget(label_pos3)
        content_layout.addWidget(label_pos2)
        content_layout.addWidget(label_pos1)

        content_box.setLayout(content_layout)
        wrapper_layout.addWidget(title_label)
        wrapper_layout.addWidget(content_box)

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
        layout.addWidget(QLabel("HUMEDAD (%)"))
        layout.addSpacing(20)
        layout.addWidget(temp_indicator)
        layout.addWidget(QLabel("TEMP (°C)"))
        layout.addStretch(1)
        return layout

    # --- 3. MÉTODO MODIFICADO ---
    def _create_graph_area(self):
        """Crea el QGroupBox y el PlotWidget para la gráfica."""

        # El QGroupBox sigue siendo el contenedor blanco
        graph_box = QGroupBox("")
        graph_box.setStyleSheet("background-color: white; color: black;")

        graph_layout = QVBoxLayout()

        # --- REEMPLAZAMOS EL QLABEL ---
        # placeholder_label = QLabel("AQUÍ VA LA GRÁFICA")

        # Creamos el widget de gráfica
        self.plot_widget = pg.PlotWidget()

        # --- Configuramos el gráfico ---
        self.plot_widget.setLabel('left', 'Valor')
        self.plot_widget.setLabel('bottom', 'Tiempo (lecturas)')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)

        # Creamos las líneas (curvas) y las guardamos
        # Usamos colores similares a tu imagen de ejemplo

        # Curva de Temperatura
        self.temp_curve = self.plot_widget.plot(
            pen=pg.mkPen('#ff5733', width=2),
            #name='Temperatura (°C)',
            fillLevel=0,
            fillBrush=(255, 87, 51, 70)  # Relleno rojo (RGBA)
        )

        # Curva de Humedad
        self.hum_curve = self.plot_widget.plot(
            pen=pg.mkPen('#2196f3', width=2),
            #name='Humedad (%)',
            fillLevel=0,
            fillBrush=(33, 150, 243, 70)  # Relleno azul (RGBA)
        )

        graph_layout.addWidget(self.plot_widget)
        # --- FIN DE LA MODIFICACIÓN ---

        graph_box.setLayout(graph_layout)
        graph_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        return graph_box

    # --- (Método _create_bottom_bar sin cambios) ---
    def _create_bottom_bar(self):
        layout = QHBoxLayout()
        self.fecha_hora_display = QLineEdit()
        self.fecha_hora_display.setPlaceholderText("FECHA Y HORA")
        self.fecha_hora_display.setReadOnly(True)
        self.ip_display = QLineEdit()
        self.ip_display.setPlaceholderText("IP DEL ARDUINO")
        self.ip_display.setReadOnly(True)
        self.importar_btn = QPushButton("EXPORTAR")
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