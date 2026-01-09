import cv2
import time
import requests
import os
import RPi.GPIO as GPIO
import dht11 

IP_LAPTOP = "192.168.10.177" 
SERVER_URL = f"http://{IP_LAPTOP}:5000/api/update"

TELEGRAM_TOKEN = 'xxxxxx'
TELEGRAM_CHAT_ID = 'xxxx'

PIN_MQ2 = 21       # Sensor Asap
PIN_FLAME = 20     # Sensor Api
PIN_BUZZER = 16    # Buzzer
PIN_DHT = 4        # Sensor Suhu (GPIO 4)

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup() # Bersihkan sisa settingan lama agar tidak error
GPIO.setup(PIN_MQ2, GPIO.IN)
GPIO.setup(PIN_FLAME, GPIO.IN)
GPIO.setup(PIN_BUZZER, GPIO.OUT)
GPIO.output(PIN_BUZZER, GPIO.LOW) 

sensor_suhu = dht11.DHT11(pin=PIN_DHT)

print(f"🔥 MONITORING AKTIF! Server: {IP_LAPTOP}")

# --- FUNGSI TELEGRAM ---
def kirim_telegram(pesan, path_foto=None):
    if not TELEGRAM_TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': pesan})
        if path_foto and os.path.exists(path_foto):
            url_foto = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(path_foto, 'rb') as f:
                requests.post(url_foto, data={'chat_id': TELEGRAM_CHAT_ID}, files={'photo': f})
    except Exception as e:
        print(f"Gagal Telegram: {e}")

# --- LOOP UTAMA ---
last_notif = 0
temp = 0
hum = 0

try:
    while True:
        result = sensor_suhu.read()
        if result.is_valid():
            temp = result.temperature
            hum = result.humidity
        
        is_gas = GPIO.input(PIN_MQ2) == 0   
        is_fire = GPIO.input(PIN_FLAME) == 0

        status_gas = "BAHAYA" if is_gas else "AMAN"
        status_api = "TERDETEKSI API" if is_fire else "AMAN"

        print(f"Suhu: {temp}C | Gas: {status_gas} | Api: {status_api}")

        # LOGIKA BAHAYA
        if is_gas or is_fire:
            GPIO.output(PIN_BUZZER, GPIO.HIGH)
            
            if time.time() - last_notif > 60:
                print("🚨 BAHAYA! Mengirim notifikasi...")
                foto = ambil_foto()
                msg = f"🚨 DARURAT!\nSuhu: {temp}C\nApi: {status_api}\nGas: {status_gas}"
                kirim_telegram(msg, foto)
                last_notif = time.time()
        else:
            GPIO.output(PIN_BUZZER, GPIO.LOW)

        # KIRIM KE LAPTOP
        try:
            payload = {
                "suhu": temp, "kelembapan": hum,
                "status_gas": status_gas, "status_api": status_api
            }
            requests.post(SERVER_URL, json=payload, timeout=1)
            # print("✅ Sent") # Di-comment biar terminal ga penuh
        except:
            print(f"❌ Gagal connect ke Laptop ({IP_LAPTOP}). Cek Firewall!")

        time.sleep(2)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nProgram Berhenti")