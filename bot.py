import requests
import time

BOT_TOKEN = "8631457299:AAGpZIld3nTruS4xgpWWflo1oMayajl74dI"
OWNER_ID  = 8493646452
url = f"https://api.telegram.org/bot{BOT_TOKEN}"
group_id  = None

def send_message(chat_id, text):
    requests.post(f"{url}/sendMessage", json={"chat_id": chat_id, "text": text})

def delete_webhook():
    requests.get(f"{url}/deleteWebhook")
    print("Webhook удалён")

def decline_requests_now(owner_chat_id):
    if not group_id:
        send_message(owner_chat_id, "❌ Сначала: /setgroup -100xxxxxxxxxx")
        return

    send_message(owner_chat_id, "⏳ Удаляю все заявки...")
    declined = 0
    last_user_id = None

    while True:
        params = {"chat_id": group_id, "limit": 100}
        if last_user_id:
            params["offset_user_id"] = last_user_id

        res = requests.get(f"{url}/getChatJoinRequests", params=params)
        data = res.json()
        print("Ответ getChatJoinRequests:", data)

        if not data.get("ok"):
            # Метод не поддерживается — пробуем через getUpdates
            send_message(owner_chat_id, f"❌ Ошибка: {data.get('description')}\nМетод не поддерживается Bot API.")
            return

        results = data.get("result", [])
        if not results:
            break

        for req in results:
            uid = req["from"]["id"]
            r = requests.post(f"{url}/declineChatJoinRequest", json={
                "chat_id": group_id,
                "user_id": uid,
            })
            if r.json().get("ok"):
                declined += 1
                print(f"Отклонён: {uid}")
            last_user_id = uid
            time.sleep(0.3)

        if len(results) < 100:
            break

    send_message(owner_chat_id, f"✅ Отклонено заявок: {declined}")

def process_updates(offset):
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
                    "/link — ссылка с заявками\n"
                    "/decline — отклонить все заявки\n\n"
                    "Новые заявки отклоняются автоматически."
                ))

            elif text.startswith("/setgroup"):
                parts = text.split()
                if len(parts) == 2:
                    global group_id
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
            uid  = update["chat_join_request"]["from"]["id"]
            gid  = update["chat_join_request"]["chat"]["id"]
            name = update["chat_join_request"]["from"].get("first_name", "—")

            res = requests.post(f"{url}/declineChatJoinRequest", json={
                "chat_id": gid,
                "user_id": uid,
            })
            if res.json().get("ok"):
                print(f"Авто-отклонён: {name} ({uid})")
                declined += 1

            time.sleep(0.3)

    return offset, declined

delete_webhook()
print("Бот запущен.")

offset = None
total  = 0

while True:
    try:
        offset, count = process_updates(offset)
        total += count
        if count:
            print(f"Отклонено: {count} | Всего: {total}")
        time.sleep(2)
    except Exception as e:
        print("Ошибка:", e)
        time.sleep(5)
