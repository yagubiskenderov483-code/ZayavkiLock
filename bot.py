import requests
import time
import os

BOT_TOKEN = "8631457299:AAGpZIld3nTruS4xgpWWflo1oMayajl74dI"
OWNER_ID  = 8493646452
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

        # Обработка сообщений
        if "message" in update:
            msg     = update["message"]
            text    = msg.get("text", "")
            user_id = msg["from"]["id"]
            chat_id = msg["chat"]["id"]

            # Проверка доступа
            if user_id != OWNER_ID:
                send_message(chat_id, "⛔ У вас нет доступа к этому боту.")
                continue

            if text == "/start":
                send_message(chat_id, (
                    "👋 Привет! Я бот для отклонения заявок.\n\n"
                    "Команды:\n"
                    "/link — получить ссылку-приглашение\n"
                    "/decline — отклонить все текущие заявки\n"
                    "/auto — включить авторежим (отклонять автоматически)"
                ))

            elif text == "/link":
                # Нужен chat_id группы — отправь /setgroup <chat_id> сначала
                send_message(chat_id, "Используй /setgroup <chat_id> чтобы указать группу, затем /link")

            elif text.startswith("/setgroup"):
                parts = text.split()
                if len(parts) == 2:
                    group_id = parts[1]
                    # Генерируем ссылку
                    res = requests.post(f"{url}/createChatInviteLink", json={
                        "chat_id": int(group_id),
                        "creates_join_request": True,
                    })
                    if res.json().get("ok"):
                        invite_link = res.json()["result"]["invite_link"]
                        send_message(chat_id, f"🔗 Ссылка с заявками:\n{invite_link}")
                    else:
                        send_message(chat_id, f"Ошибка: {res.json()}")
                else:
                    send_message(chat_id, "Формат: /setgroup -100xxxxxxxxxx")

        # Автоотклонение заявок
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
