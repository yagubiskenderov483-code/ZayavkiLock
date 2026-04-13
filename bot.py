import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = int(os.getenv("CHAT_ID"))
url = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    requests.post(f"{url}/sendMessage", json={"chat_id": chat_id, "text": text})

def delete_webhook():
    r = requests.get(f"{url}/deleteWebhook")
    print("Webhook удалён:", r.json().get("ok"))

def decline_all(offset):
    params = {
        "timeout": 10,
        "allowed_updates": ["chat_join_request", "message"],
    }
    if offset:
        params["offset"] = offset

    r = requests.get(f"{url}/getUpdates", params=params)
    data = r.json()

    if not data.get("ok"):
        print("Ошибка getUpdates:", data)
        return offset, 0

    updates = data.get("result", [])
    declined = 0

    for update in updates:
        offset = update["update_id"] + 1

        # Обработка /start
        if "message" in update:
            msg  = update["message"]
            text = msg.get("text", "")
            if text == "/start":
                send_message(msg["chat"]["id"], "✅ Бот работает! Автоматически отклоняю заявки в группу.")
                print("Получена команда /start")

        # Отклонение заявок
        if "chat_join_request" in update:
            user_id = update["chat_join_request"]["from"]["id"]
            chat_id = update["chat_join_request"]["chat"]["id"]
            name    = update["chat_join_request"]["from"].get("first_name", "—")

            res = requests.post(f"{url}/declineChatJoinRequest", json={
                "chat_id": chat_id,
                "user_id": user_id,
            })
            if res.json().get("ok"):
                print(f"Отклонён: {name} (id: {user_id})")
                declined += 1
            else:
                print(f"Ошибка отклонения {user_id}:", res.json())

            time.sleep(0.3)

    return offset, declined

# Запуск
delete_webhook()
print("Бот запущен. Жду заявки...")

offset = None
total  = 0

while True:
    try:
        offset, count = decline_all(offset)
        total += count
        if count:
            print(f"Отклонено за цикл: {count} | Всего: {total}")
        time.sleep(2)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(5)
