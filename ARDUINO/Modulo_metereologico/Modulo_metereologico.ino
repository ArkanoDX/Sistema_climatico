/*--------------------------------------------------------------
---------------------------Header Files-------------------------
----------------------------------------------------------------*/
#include <SPI.h>            
#include <SD.h>             
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
#define SD_CS_Pin 4         

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

// --- MODIFICADO: Estas variables ahora se asignan dinámicamente en el bucle ---
IPAddress staticIP;
IPAddress gateway;
IPAddress subnet;
IPAddress dns;

// --- MODIFICADO: Estructura para guardar toda la info de red ---
struct WifiCredential {
  const char* ssid;
  const char* pass;
  IPAddress ip;
  IPAddress gateway;
  IPAddress subnet;
  IPAddress dns;
};

// --- MODIFICADO: Arreglo con toda la info de red ---
// 
WifiCredential knownNetworks[] = {
  { // Red 1: TecNM-ITQuerétaro
    "TecNM-ITQuerétaro", "Zorros.ITQ25",
    IPAddress(172, 20, 0, 44),         // IP Estática (de tus comentarios)
    IPAddress(172, 20, 0, 1),           // <-- ¡OJO! Reemplaza con el Gateway correcto para esta red
    IPAddress(255, 255, 0, 0),          // <-- ¡OJO! Reemplaza con la Subred correcta
    IPAddress(172, 20, 0, 1)            // <-- ¡OJO! Reemplaza con el DNS correcto
  },
  { // Red 2: RED PRUEBA (usará la IP de "prueba")
    "HUAWEI-C137", "Wfi@1897", 
    IPAddress(192, 168, 3, 100),        // IP Estática (de tus comentarios)
    IPAddress(192, 168, 3, 254),        // Gateway (de tu código)
    IPAddress(255, 255, 255, 0),        // Subred (de tu código)
    IPAddress(192, 168, 3, 254)         // DNS (de tu código)
  },
  { // Red 3: Red TecNorte (usará la IP "tercera red")
    "SSID_RED-DE_PRUEBA", "CONTRASEÑÁ", 
    IPAddress(0, 0, 0, 0),              // IP (como pediste)
    IPAddress(0, 0, 0, 0),              // (No importa si la IP es 0)
    IPAddress(0, 0, 0, 0),              // (No importa)
    IPAddress(0, 0, 0, 0)               // (No importa)
  }
};


// --- Variables globales (sin cambios) ---
const uint32_t wifi_connected[] = {0x3f840, 0x49f22084, 0xe4110040}; 
const uint32_t no_wifi[] = {0x403f844, 0x49f22484, 0xe4110040}; 
char ssid[64]; 
char pass[64]; 
float temperature = 0.0, humidity = 0.0, pressure = 0.0; 
int AQI = 0, rainfall = 0; 
unsigned long lastSensorUpdate = 0; 
unsigned long lastWiFiCheck = 0; 

bool isRaining = false; 
int servoPos = 0; 
int targetServoPos = 0; 
unsigned long lastServoMove = 0; 
const int servoInterval = 1; 
bool sdCardInitialized = false; 

/*---------------------------------------------------------------------
-----------------User Defined Functions--------------------------------
---------------------------------------------------------------------------*/

// --- (updateServo y get_wifi_credentials sin cambios) ---
void updateServo() {
  if (servoPos == targetServoPos) { return; 
  }
  if (millis() - lastServoMove >= servoInterval) { 
    lastServoMove = millis(); 
    if (servoPos < targetServoPos) { 
      servoPos++;
      myServo.write(servoPos); 
    } else if (servoPos > targetServoPos) { 
      servoPos--;
      myServo.write(servoPos); 
    }
  }
}

void get_wifi_credentials() {
  while (Serial.available() > 0) { Serial.read(); 
  }
  Serial.println("Por favor, ingrese el nombre de la red WiFi (SSID) y presione Enter:"); 
  while (Serial.available() == 0) {} 
  String ssid_str = Serial.readStringUntil('\n');
  ssid_str.trim();
  ssid_str.toCharArray(ssid, sizeof(ssid));
  Serial.print("SSID recibido: ");
  Serial.println(ssid); 
  Serial.println("\nAhora, ingrese la contraseña de la red WiFi y presione Enter:"); 
  for (int i = 0; i < 91; ++i) { Serial.print("-"); } 
  Serial.println(); 
  while (Serial.available() == 0) {} 
  String pass_str = Serial.readStringUntil('\n');
  pass_str.trim();
  pass_str.toCharArray(pass, sizeof(pass));
  Serial.println("Contraseña recibida. Intentando conectar..."); 
}

// --- (wifi_connect sin cambios, usará las variables globales) ---
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
  
  WiFi.config(staticIP, dns, gateway, subnet); 
  
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
  
  matrix.loadFrame(wifi_connected); 
  return true;
}

// --- (wifi_reconnect sin cambios) ---
void wifi_reconnect() {
  Serial.println("Se perdió la conexión WiFi. Reconectando...");
  matrix.loadFrame(no_wifi); 
  delay(1000); 
  if (wifi_connect()) { 
    Serial.println("\n¡Reconexión exitosa!");
    Serial.print("Nueva dirección IP: ");
    Serial.println(WiFi.localIP()); 
  }
}

// --- (logDataToSD sin cambios) ---
void logDataToSD() {
  if (!sdCardInitialized) { return; }  
  File dataFile = SD.open("datalog.csv", FILE_WRITE); 
  if (dataFile) { 
    String dataString = "";
    dataString += String(temperature); 
    dataString += ",";
    dataString += String(humidity); 
    dataString += ","; 
    dataString += String(pressure); 
    dataString += ",";
    dataString += String(AQI); 
    dataString += ",";
    dataString += String(rainfall); 
    dataFile.println(dataString);
    dataFile.close(); 
  } else {
    Serial.println("Error al abrir datalog.csv para escribir"); 
  }
}

// --- (read_sensor_data sin cambios) ---
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

  int rainReading = digitalRead(Rain_SensorPin); 
  if (rainReading == LOW) { 
    rainfall = 1;
    isRaining = true;
    targetServoPos = 132; 
  } else { 
    rainfall = 0;
    isRaining = false;
    targetServoPos = 0; 
  }
  
  logDataToSD(); 
}

// --- (send_json_data sin cambios) ---
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

/*-----------------------------------------------------------------
----------------------Estructura de la pagina web -----------------
-----------------------------------------------------------------*/

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
            margin: 0;
        }
        .container { 
            max-width: 900px; 
            margin: auto; 
        }
        .data-container { 
            display: flex; 
            flex-direction: column; 
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
        <div id='weather' class='data-container'>
            </div>
        <div class='graph'>
            <canvas id='combinedGraph'></canvas>
        </div>
    </div>
    
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    
    <script>
        const ctxCombined = document.getElementById('combinedGraph').getContext('2d');
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
                        title: { 
                            display: true, 
                            text: 'Tiempo' // Título del eje X
                        } 
                    }, 
                    y: { 
                        beginAtZero: true, 
                        min: 0, 
                        max: 100, 
                        ticks: { 
                            stepSize: 10 
                        } 
                    } 
                } 
            }
        });

        // Función para pedir datos al Arduino
        function fetchWeatherData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    // Actualiza las tarjetas de datos
                    document.getElementById('weather').innerHTML = `
                        <div class='data-card'>
                            🌡️ Temp: ${data.temperature}°C &nbsp;&nbsp;&nbsp; 
                            🌨️ Humedad: ${data.humidity}%
                        </div>
                        <div class='data-card'>
                            🌀 Presión: ${data.pressure} mbar 
                        </div>
                        <div class='data-card'>
                            🌪️ AQI: ${data.aqi} &nbsp;&nbsp;&nbsp; 
                            🌧️ Lluvia: ${data.rainfall ? 'Sí' : 'No'}
                        </div>`; 
                    
                    // Actualiza el gráfico
                    let time = new Date().toLocaleTimeString();
                    combinedChart.data.labels.push(time);
                    combinedChart.data.datasets[0].data.push(data.temperature);
                    combinedChart.data.datasets[1].data.push(data.humidity);
                    
                    // Limita el gráfico a 10 puntos
                    if (combinedChart.data.labels.length > 10) {
                        combinedChart.data.labels.shift();
                        combinedChart.data.datasets[0].data.shift();
                        combinedChart.data.datasets[1].data.shift();
                    }
                    combinedChart.update();
                })
                .catch(error => {
                     console.error("Error al obtener datos:", error);
                });
        }        
        
        // Pide datos cada 2 segundos
        setInterval(fetchWeatherData, 2000);
    </script>
</body>
</html>
)rawliteral"; 
  client.print(html);
}

// --- (run_local_webserver sin cambios) ---
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
  myServo.attach(Servo_Pin); 
  myServo.write(servoPos); 

  // Inicializar SD
  if (!SD.begin(SD_CS_Pin)) { 
    sdCardInitialized = false; 
  } else {
    sdCardInitialized = true; 
    File dataFile = SD.open("datalog.csv", FILE_WRITE); 
    if (dataFile && dataFile.size() == 0) { 
      dataFile.println("Temperatura,Humedad,Presion,QAI,Lluvia");
    }
    dataFile.close(); 
  }

  bool isConnected = false; 
  int numKnownNetworks = sizeof(knownNetworks) / sizeof(knownNetworks[0]); 
  Serial.println("Buscando redes WiFi conocidas..."); 

  // --- BUCLE MODIFICADO ---
  for (int i = 0; i < numKnownNetworks; i++) {
    // Asigna el SSID y Pass
    strncpy(ssid, knownNetworks[i].ssid, sizeof(ssid)); 
    strncpy(pass, knownNetworks[i].pass, sizeof(pass)); 
    ssid[sizeof(ssid) - 1] = '\0'; 
    pass[sizeof(pass) - 1] = '\0'; 

    // --- NUEVO: Asigna las IPs globales para esta red ---
    staticIP = knownNetworks[i].ip;
    gateway = knownNetworks[i].gateway;
    subnet = knownNetworks[i].subnet;
    dns = knownNetworks[i].dns;
    
    // Ahora llama a wifi_connect(), que usará las variables globales que acabamos de asignar
    if (wifi_connect()) { 
      isConnected = true;
      break; 
    } else {
      Serial.println("... intento fallido."); 
      WiFi.disconnect(); 
      delay(100); 
    }
  }
  // --- FIN DE LA MODIFICACIÓN ---

  // Si ninguna red conocida funcionó, pedir credenciales manualmente
  if (!isConnected) {
    Serial.println("\nNo se pudo conectar a ninguna red conocida."); 
    get_wifi_credentials(); 
    isConnected = wifi_connect(); 
  }

  // Continuar con el resto del setup SÓLO SI hay conexión
  if (isConnected) {
    Serial.println("\n¡Conexión a WiFi e IP obtenida exitosamente!"); 
    Serial.print("Red conectada: "); 
    Serial.println(ssid); 
    Serial.print("Dirección IP asignada: "); 
    Serial.println(WiFi.localIP()); 
    Serial.print("Potencia de la señal (RSSI): "); 
    Serial.print(WiFi.RSSI()); 
    Serial.println(" dBm"); 
    server.begin(); 
    Serial.println("Servidor web iniciado."); 
    
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
  } 
  
  Serial.println("================================================"); 
  if (!sdCardInitialized) {
      Serial.println("No se sincronizo la SD"); 
  }
  
  Serial.println("--- Setup Completado ---"); 
}

/*-----------------------------------------------------------
-----------------Loop function-------------------------------
-------------------------------------------------------------*/
void loop() {
  if (millis() - lastSensorUpdate >= 2000) {  
    lastSensorUpdate = millis();
    read_sensor_data(); 
  }

  updateServo(); 

  if (WiFi.status() != WL_CONNECTED && millis() - lastWiFiCheck >= 5000) { 
    lastWiFiCheck = millis();
    wifi_reconnect(); 
  }

  run_local_webserver(); 
}