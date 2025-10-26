from PyQt5.QtWidgets import QFileDialog
from openpyxl import Workbook
from collections import deque


def export_data_to_excel(parent_window, status_bar,
                         temp_history: deque,
                         hum_history: deque,
                         pres_history: deque,
                         qai_history: deque):
    """
    Abre un diálogo "Guardar como" y exporta el historial
    de datos de los sensores a un archivo .xlsx.
    """

    status_bar.showMessage("Generando archivo de Excel...")

    # 1. Pedir al usuario dónde guardar el archivo
    options = QFileDialog.Options()
    filePath, _ = QFileDialog.getSaveFileName(parent_window, "Guardar Archivo", "",
                                              "Archivos de Excel (*.xlsx);;Todos los archivos (*)", options=options)

    if not filePath:
        # Si el usuario presionó "Cancelar"
        status_bar.showMessage("Exportación cancelada.")
        return

    # 2. Crear el libro de Excel en memoria
    wb = Workbook()
    ws = wb.active
    ws.title = "Datos de Sensores"

    # 3. Escribir los encabezados
    ws.append(["Temperatura (°C)", "Humedad (%)", "Presión (mbar)", "QAI"])

    # 4. Escribir los datos
    temp_data = list(temp_history)
    hum_data = list(hum_history)
    pres_data = list(pres_history)
    qai_data = list(qai_history)

    for i in range(len(temp_data)):
        ws.append([
            temp_data[i] if i < len(temp_data) else None,
            hum_data[i] if i < len(hum_data) else None,
            pres_data[i] if i < len(pres_data) else None,
            qai_data[i] if i < len(qai_data) else None
        ])

    # 5. Guardar el archivo en el disco
    try:
        wb.save(filePath)
        status_bar.showMessage(f"¡Datos exportados exitosamente!")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")
        status_bar.showMessage(f"Error al guardar el archivo.")