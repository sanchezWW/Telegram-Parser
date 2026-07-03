import json
import time
import requests

URL = "http://localhost:8000/telegram/connect"
PHONE = "+7123456789"

# Перебираем все возможные порты мобильных и локальных прокси-клиентов
POSSIBLE_PORTS = [10808]
PROXY_TYPES = ["socks5"]

def try_connect():
    print("Запуск автоматического тестирования подключения к Telegram...")
    
    for proxy_type in PROXY_TYPES:
        for port in POSSIBLE_PORTS:
            payload = {
                "phone": PHONE,
                "proxy": {
                    "type": proxy_type,
                    "host": "127.0.0.1",
                    "port": port,
                    "username": "",
                    "password": ""
                }
            }
            
            print(f"\n Проверка конфигурации: {proxy_type.upper()} через порт {port}...")
            
            try:
                # Увеличиваем timeout до 65 секунд, так как Telethon долго проверяет порты
                response = requests.post(URL, json=payload, timeout=5)
                print(f"Статус ответа сервера: {response.status_code}")
                print(f"Ответ API: {response.text}")
                
            except requests.exceptions.ReadTimeout:
                print(f" Сервер думает... Проверьте логи в окне run.py!")
                print("Если там написано 'Proxy connection timed out', это нормально, ждем следующий порт...")
                time.sleep(5)
                
            except requests.exceptions.RequestException as e:
                print(f" Критическая ошибка: {e}")
                return

if __name__ == "__main__":
    try_connect()