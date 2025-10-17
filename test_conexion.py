import requests

# ---------------------------------------------------------------------
# PASO 1: Pega aquí la IP que ves en el Monitor Serie de tu Arduino
ARDUINO_IP = "192.168.3.184"  # <--- ¡CAMBIA ESTA LÍNEA!
# ---------------------------------------------------------------------

# Construimos la URL para pedir los datos
url = f"http://{ARDUINO_IP}/data"

print(f"Intentando conectar con el Arduino en: {url}")

try:
    # Hacemos la petición con un tiempo de espera de 5 segundos
    response = requests.get(url, timeout=5)

    # Verificamos si la respuesta fue exitosa (código 200 OK)
    response.raise_for_status()

    # Si todo fue bien, imprimimos los datos
    data = response.json()
    print("\n¡CONEXIÓN EXITOSA! ✅")
    print("Datos recibidos:")
    print(data)

except requests.exceptions.Timeout:
    print("\nFALLO LA CONEXIÓN: Timeout.")
    print("El Arduino no respondió a tiempo. Causa probable: Aislamiento de AP en el router o IP incorrecta.")

except requests.exceptions.ConnectionError:
    print("\nFALLO LA CONEXIÓN: Connection Error.")
    print(
        "No se pudo establecer una conexión. Revisa que la IP sea correcta y que ambos dispositivos estén en la misma red.")

except requests.exceptions.RequestException as e:
    print(f"\nOcurrió un error inesperado: {e}")