/*--------------------------------------------------------------
---------------------------Header Files-------------------------
----------------------------------------------------------------*/
#include <Adafruit_BMP085.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>
#include "Arduino_LED_Matrix.h"
#include "WiFiS3.h"
#include <WiFiUdp.h>
#include <ArduinoMDNS.h>
#include <Servo.h>

/*-----------------------------------------------------------------------
-------------------------Sensor pin definition Macros-------------------
-------------------------------------------------------------------------*/
#define Rain_SensorPin 3
#define Air_SensorPin A1
#define Temp_Hum_SensorPin 2
#define Servo_Pin 9

/*-------------------------------------------------------------------------
--------------------------Object instantiation-----------------------------
--------------------------------------------------------------------------*/
DHT_Unified dht(Temp_Hum_SensorPin, DHT11);
Adafruit_BMP085 bmp;
WiFiServer server(80);
ArduinoLEDMatrix matrix;
WiFiUDP udp;
MDNS mdns(udp);
Servo myServo;

/*--------------------------------------------------------------------
-------------------------Global variables----------------------------
----------------------------------------------------------------------*/

// --- INICIO: Redes WiFi conocidas ---
struct WifiCredential {
  const char* ssid;
  const char* pass;
};

WifiCredential knownNetworks[] = {
  {"ITQ-Alumnos", "ITQ.Alumnos2013"},
  {"SSID_DE_TU_OFICINA", "CONTRASEÑA_OFICINA"},
  {"SSID_DE_TU_CELULAR", "CONTRASEÑA_CELULAR"}
};

const uint32_t wifi_connected[] = {0x3f840, 0x49f22084, 0xe4110040};
const uint32_t no_wifi[] = {0x403f844, 0x49f22484, 0xe4110040};
char ssid[64];
char pass[64];
float temperature = 0.0, humidity = 0.0, pressure = 0.0;
int AQI = 0, rainfall = 0;
unsigned long lastSensorUpdate = 0;
unsigned long lastWiFiCheck = 0;

bool isRaining = false;

// --- lógica de servo (Compuerta) ---
int servoPos = 0;              // Posición actual (inicia en reposo en 0)
int targetServoPos = 0;        // Posición deseada (0=Abierto, 132=Cerrado)
unsigned long lastServoMove = 0; // Tiempo del último movimiento
const int servoInterval = 1;    // ms entre cada paso del servo

/*---------------------------------------------------------------------
-----------------User Defined Functions--------------------------------
---------------------------------------------------------------------------*/

// --- MODIFICADO: Nueva función updateServo (Compuerta) ---
// Esta función debe ser llamada en CADA iteración del loop()
void updateServo() {
  
  // Revisa si la posición actual es diferente de la posición objetivo
  if (servoPos == targetServoPos) {
    return; // No hay nada que mover, salir
  }

  // Revisa si ya pasó el tiempo para el siguiente paso (15ms)
  if (millis() - lastServoMove >= servoInterval) {
    lastServoMove = millis(); // Resetea el temporizador

    if (servoPos < targetServoPos) {
      servoPos++; // Mover hacia arriba (cerrar)
      myServo.write(servoPos);
      
    } else if (servoPos > targetServoPos) {
      servoPos--;   // Mover hacia abajo (abrir)
      myServo.write(servoPos);
    }
  }
}


void get_wifi_credentials() {
  while (Serial.available() > 0) {
    Serial.read();
  }
  Serial.println("Por favor, ingrese el nombre de la red WiFi (SSID) y presione Enter:");
  while (Serial.available() == 0) {}
  String ssid_str = Serial.readStringUntil('\n');
  ssid_str.trim();
  ssid_str.toCharArray(ssid, sizeof(ssid));
  Serial.print("SSID recibido: ");
  Serial.println(ssid);
  Serial.println("\nAhora, ingrese la contraseña de la red WiFi y presione Enter:");
  /*-------------------------------------------------------------------------------
  ---------------Salto de linea en el serial monitor-------------------------------
  ---------------------------------------------------------------------------------*/
  for (int i = 0; i < 91; ++i) {
    Serial.print("-");
  }
  Serial.println();
/*-------------------------------------------------------------------------------
  ---------------Salto de linea en el serial monitor-------------------------------
  ---------------------------------------------------------------------------------*/

  while (Serial.available() == 0) {}
  String pass_str = Serial.readStringUntil('\n');
  pass_str.trim();
  pass_str.toCharArray(pass, sizeof(pass));
  Serial.println("Contraseña recibida. Intentando conectar...");
}

bool wifi_connect() {
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Error de comunicación con el módulo WiFi.");
    matrix.loadFrame(no_wifi);
    return false;
  }

  Serial.print("Intentando conectar a la red WiFi: ");
  Serial.println(ssid);
  matrix.loadSequence(LEDMATRIX_ANIMATION_WIFI_SEARCH);
  matrix.play(true);
  
  WiFi.begin(ssid, pass);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 15) {
    Serial.print(".");
    delay(1000);
    attempts++;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nNo se pudo conectar a la red WiFi (Timeout).");
    matrix.loadFrame(no_wifi);
    return false;
  }

  // --- A la espera de la IP ---
  Serial.println("\n¡Conectado a la red! Esperando dirección IP...");
  int ip_attempts = 0;
  while (WiFi.localIP() == IPAddress(0,0,0,0) && ip_attempts < 10) {
     Serial.print("DHCP.");
     Serial.println();
     /*-------------------------------------------------------------------------------
---------------Salto de linea en el serial monitor-------------------------------
---------------------------------------------------------------------------------*/
     for (int i = 0; i < 91; ++i) {
     Serial.print("-");
     }
     Serial.println();
/*-------------------------------------------------------------------------------
---------------Salto de linea en el serial monitor-------------------------------
---------------------------------------------------------------------------------*/
     delay(500);
     // Este delay() también está bien aquí
     ip_attempts++;
  }

  if (WiFi.localIP() == IPAddress(0,0,0,0)) {
     Serial.println("\nFallo al obtener IP. La IP es 0.0.0.0");
     matrix.loadFrame(no_wifi);
     return false;
  }

  matrix.loadFrame(wifi_connected);
  return true;
}


void wifi_reconnect() {
  Serial.println("Se perdió la conexión WiFi. Reconectando...");
  matrix.loadFrame(no_wifi);
  delay(1000);
  if (wifi_connect()) { // Intentará reconectar a la *última* red exitosa
    Serial.println("\n¡Reconexión exitosa!");
    Serial.print("Nueva dirección IP: ");
    Serial.println(WiFi.localIP());
  }
}

void read_sensor_data() {
  sensors_event_t event;
  dht.temperature().getEvent(&event);
  if (!isnan(event.temperature)) {
    temperature = event.temperature;
  }

  dht.humidity().getEvent(&event);
  if (!isnan(event.relative_humidity)) {
    humidity = event.relative_humidity;
  }

  pressure = bmp.readPressure() / 100.0;
  int mq135Raw = analogRead(Air_SensorPin);
  AQI = map(mq135Raw, 0, 1023, 0, 300);

  // --- MODIFICADO: NUEVA LÓGICA DE LLUVIA (COMPUERTA) ---
  int rainReading = digitalRead(Rain_SensorPin);
  
  if (rainReading == LOW) { // Está lloviendo
    rainfall = 1;
    isRaining = true;
    targetServoPos = 132; // ¡OBJETIVO: CERRAR COMPUERTA!
    
  } else { // No está lloviendo
    rainfall = 0;
    isRaining = false;
    targetServoPos = 0;   // ¡OBJETIVO: ABRIR COMPUERTA!
  }

}

void send_json_data(WiFiClient & client) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.println();
  String json = "{\"temperature\":" + String(temperature) +
           ",\"humidity\":" + String(humidity) +
           ",\"pressure\":" + String(pressure) +
           ",\"aqi\":" + String(AQI) +
           ",\"rainfall\":" + String(rainfall) + "}";
  client.println(json);
}

void send_web_page(WiFiClient & client) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/html");
  client.println("Connection: close");
  client.println();
  const char* html = R"rawliteral(
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema Climatico TecNM</title>
    
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1f2177;
            color: #333;
            text-align: center;
      
 
             padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: auto;
        }
        .data-container {
            display: flex;
            
 flex-direction: 
 column;
       
             gap: 10px;
        }
        .data-card {
            background: #fff;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, .1);
  
   
             flex: 1;
      
             margin: 5px;
            text-align: center;
        }
        .graph {
            background: #fff;
 padding: 15px;
 border-radius: 8px;
 box-shadow: 0 4px 8px rgba(0, 0, 0, .1);
            margin-top: 15px;
        }
        canvas {
            width: 100%;
 height: 400px;
        }
        .title-container {
            display: flex;
 justify-content: center;
            align-items: center;
            gap: 30px;
            margin-bottom: 20px;
        }
        .title-container h1 {
            font-size: 2rem;
 color: #fff;
            margin: 0;
        }
        .title-container img {
            width: 80px;
 height: auto;
        }
    </style>
</head>
<body>

    <div class="title-container">
        <h1>Sistema Climatico TecNm</h1>
        </div>
    
    <div class='container'>
        <div id='weather' class='data-container'></div>
        
        <div class='graph'>
            <canvas id='combinedGraph'></canvas>
    
 
         </div>
    </div>
    
 
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    
    <script>
        const ctxCombined = document.getElementById('combinedGraph').getContext('2d');
 // --- Configuración de la Gráfica (ahora ordenada) ---
        const combinedChart = new Chart(ctxCombined, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                   
 
 
   {
                        label: 'Temperatura (°C)',
                        data: [],
                        borderColor: '#ff5733',
                    
  
   
   backgroundColor: 'rgba(255, 87, 51, 0.2)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3
              
   
     
  },
                    {
                        label: 'Humedad (%)',
                        data: [],
                    
    
  borderColor: '#2196f3',
    
                         backgroundColor: 'rgba(33, 150, 243, 0.2)',
                        fill: true,
                        tension: 0.4,
           
     
          pointRadius: 3
 
                     }
                ]
            },
            options: {
                responsive: true,
     
       
       maintainAspectRatio: false,
      
                 animation: false,
                scales: {
                    x: {
                        title: 
 { display: true, text: 'Time' }
 
                     },
 
                     y: {
                        beginAtZero: true,
                        min: 
 0,     
                 max: 100,
     
                         ticks: { stepSize: 10 }
                    }
                }
    
         }
 
        });
 // --- Función para pedir datos y actualizar la página ---
        function fetchWeatherData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
             // 1. Actualizar el HTML de las tarjetas (ahora más legible)
                    document.getElementById('weather').innerHTML = `
                        <div class='data-card'>     
 🌡️ Temp: ${data.temperature}°C &nbsp;&nbsp;&nbsp; 🌨️ Humedad: ${data.humidity}%
                        </div>
                        <div class='data-card'>
                            🌀 Presión: ${data.pressure} mbar 
     </div>
                        <div class='data-card'>
                            🌪️ AQI: ${data.aqi} &nbsp;&nbsp;&nbsp; 🌧️ Lluvia: ${data.rainfall ? 'Yes' : 'No'}                       
   </div>          
             `;                    
                    // 2. Actualizar los datos de la gráfica
                    let time = new 
 Date().toLocaleTimeString();
 combinedChart.data.labels.push(time);
                    combinedChart.data.datasets[0].data.push(data.temperature);
                    combinedChart.data.datasets[1].data.push(data.humidity);
                    
                    // 3. Limitar la gráfica a 10 puntos
                    if (combinedChart.data.labels.length > 10) {
                        combinedChart.data.labels.shift();
 combinedChart.data.datasets[0].data.shift();
                        combinedChart.data.datasets[1].data.shift();
                    }
                    // 4. Redibujar la gráfica
                    combinedChart.update();
 });
        }        
        // --- CORRECCIÓN 2: Intervalo de JS alineado con el sensor ---
        // Pedir datos cada 2 segundos (2000ms) para coincidir con la actualización del sensor
        setInterval(fetchWeatherData, 2000);
 // --- FIN CORRECCIÓN 2 ---
 </script>
</body>
</html>
)rawliteral";
  client.print(html);
}

void run_local_webserver() {
  WiFiClient client = server.available();
  if (client) {
    String request = client.readStringUntil('\r');
    client.flush();
    if (request.indexOf("GET / ") != -1) {
      send_web_page(client);
    } else if (request.indexOf("GET /data") != -1) {
      send_json_data(client);
    }
    client.stop();
  }
}

/*-----------------------------------------------------------------
-----------------------Setup Function------------------------------
------------------------------------------------------------------*/
void setup() {
  Serial.begin(115200);
  while (!Serial);
  Serial.println("--- Inicio del Setup ---");

  matrix.begin();
  
  // --- NUEVO --- Inicializar el servo
 
  myServo.attach(Servo_Pin);
  myServo.write(servoPos); // Lo coloca en la posición inicial (0 grados) al iniciar

  bool isConnected = false;
  // Bandera para saber si ya nos conectamos
  int numKnownNetworks 
 = sizeof(knownNetworks) / sizeof(knownNetworks[0]);

  Serial.println("Buscando redes WiFi conocidas...");
  // 1. Intentar conectar a las redes conocidas
  for (int i = 0;
 i < numKnownNetworks; i++) {
    // La función wifi_connect() usa las variables globales 'ssid' y 'pass'
    strncpy(ssid, knownNetworks[i].ssid, sizeof(ssid));
    strncpy(pass, knownNetworks[i].pass, sizeof(pass));
    ssid[sizeof(ssid) - 1] = '\0';
    pass[sizeof(pass) - 1] = '\0';
    if (wifi_connect()) {
      isConnected = true;
      break;
    } else {
      Serial.println("... intento fallido.");
      WiFi.disconnect();
      delay(100);
    }
  }

  // 2. Si ninguna red conocida funcionó, pedir credenciales manualmente
  if (!isConnected) {
    Serial.println("\nNo se pudo conectar a ninguna red conocida.");
    get_wifi_credentials();
    isConnected = wifi_connect();
  }

  // 3. Continuar con el resto del setup SÓLO SI hay conexión
  if (isConnected) {
    Serial.println("\n¡Conexión a WiFi e IP obtenida exitosamente!");
    Serial.print("Red conectada: ");
    Serial.println(ssid); // Muestra a cuál red se conectó
    Serial.print("Dirección IP asignada: ");
    Serial.println(WiFi.localIP());
    Serial.print("Potencia de la señal (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    server.begin();
    Serial.println("Servidor web iniciado. Puede acceder desde la IP de arriba.");
    if (!mdns.begin("sistemaclima-tecnm")) {
      Serial.println("Error al iniciar MDNS.");
    } else {
      mdns.addServiceRecord("_http._tcp", 80, (MDNSServiceProtocol_t)1);
    }
  } else {
    Serial.println("FALLO EN LA CONEXIÓN. No se pudo conectar a redes conocidas ni manuales.");
  }

  pinMode(Rain_SensorPin, INPUT);
  pinMode(Air_SensorPin, INPUT);
  dht.begin();
  if (!bmp.begin()) {
    Serial.println("No se encontró el sensor BMP085, revisar conexiones.");
  } else {
    Serial.println("--- Setup Completado ---");
  }
}

/*-----------------------------------------------------------
-----------------Loop function-------------------------------
-------------------------------------------------------------*/
void loop() {
  if (millis() - lastSensorUpdate >= 2000) { 
    lastSensorUpdate = millis();
    read_sensor_data();
  }

  // Esto revisará si el servo necesita moverse un paso, sin bloquear
  updateServo();
  // --- FIN MODIFICADO ---

  // Si se pierde la conexión, wifi_reconnect() intentará
  // reconectarse a la última red exitosa (guardada en 'ssid' y 'pass')
  if (WiFi.status() != WL_CONNECTED && millis() - lastWiFiCheck >= 5000) {
    lastWiFiCheck = millis();
    wifi_reconnect();
  }

  run_local_webserver();
}