import requests
import time

BOT_TOKEN = "8631457299:AAGpZIld3nTruS4xgpWWflo1oMayajl74dI"
OWNER_ID  = 8493646452
url = f"https://api.telegram.org/bot{BOT_TOKEN}"

group_id = None  # сохраняется после /setgroup

def send_message(chat_id, text):
    requests.post(f"{url}/sendMessage", json={"chat_id": chat_id, "text": text})

def delete_webhook():
    r = requests.get(f"{url}/deleteWebhook")
    print("Webhook удалён:", r.json().get("ok"))

def decline_requests_now(chat_id):
    global group_id
    if not group_id:
        send_message(chat_id, "❌ Сначала укажи группу: /setgroup -100xxxxxxxxxx")
        return

    send_message(chat_id, "⏳ Отклоняю заявки...")
    
    # Получаем участников через getUpdates не работает для старых заявок
    # Используем pending requests напрямую
    declined = 0
    offset_req = None
    
    while True:
        params = {"chat_id": group_id, "limit": 100}
        if offset_req:
            params["offset_user_id"] = offset_req
            
        res = requests.get(f"{url}/getChatJoinRequests", params=params)
        data = res.json()
        
        if not data.get("ok") or not data.get("result"):
            break
            
        for req in data["result"]:
            uid = req["from"]["id"]
            requests.post(f"{url}/declineChatJoinRequest", json={
                "chat_id": group_id,
                "user_id": uid,
            })
            declined += 1
            offset_req = uid
            time.sleep(0.3)
            
        if len(data["result"]) < 100:
            break

    send_message(chat_id, f"✅ Отклонено заявок: {declined}")

def decline_all(offset):
    global group_id
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

        if "message" in update:
            msg     = update["message"]
            text    = msg.get("text", "")
            user_id = msg["from"]["id"]
            chat_id = msg["chat"]["id"]

            if user_id != OWNER_ID:
                send_message(chat_id, "⛔ Нет доступа.")
                continue

            if text == "/start":
                send_message(chat_id, (
                    "👋 Привет!\n\n"
                    "/setgroup -100xxx — указать группу\n"
                    "/link — получить ссылку с заявками\n"
                    "/decline — отклонить все заявки сейчас\n\n"
                    "Новые заявки отклоняются автоматически."
                ))

            elif text.startswith("/setgroup"):
                parts = text.split()
                if len(parts) == 2:
                    group_id = int(parts[1])
                    send_message(chat_id, f"✅ Группа установлена: {group_id}")
                else:
                    send_message(chat_id, "Формат: /setgroup -100xxxxxxxxxx")

            elif text == "/link":
                if not group_id:
                    send_message(chat_id, "❌ Сначала: /setgroup -100xxxxxxxxxx")
                else:
                    res = requests.post(f"{url}/createChatInviteLink", json={
                        "chat_id": group_id,
                        "creates_join_request": True,
                    })
                    if res.json().get("ok"):
                        link = res.json()["result"]["invite_link"]
                        send_message(chat_id, f"🔗 Ссылка:\n{link}")
                    else:
                        send_message(chat_id, f"Ошибка: {res.json()}")

            elif text == "/decline":
                decline_requests_now(chat_id)

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
                print(f"Ошибка: {res.json()}")

            time.sleep(0.3)

    return offset, declined

delete_webhook()
print("Бот запущен.")

offset = None
total  = 0

while True:
    try:
        offset, count = decline_all(offset)
        total += count
        if count:
            print(f"Отклонено: {count} | Всего: {total}")
        time.sleep(2)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(5)
