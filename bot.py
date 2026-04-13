import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = int(os.getenv("CHAT_ID"))
url = f"https://api.telegram.org/bot{BOT_TOKEN}"

def decline_all():
    declined = 0
    offset = None

    while True:
        params = {"timeout": 10, "allowed_updates": ["chat_join_request"]}
        if offset:
            params["offset"] = offset

        r = requests.get(f"{url}/getUpdates", params=params)
        updates = r.json().get("result", [])

        if not updates:
            print(f"Новых заявок нет. Отклонено за сессию: {declined}")
            break

        for update in updates:
            offset = update["update_id"] + 1
            if "chat_join_request" in update:
                user_id = update["chat_join_request"]["from"]["id"]
                chat_id = update["chat_join_request"]["chat"]["id"]

                res = requests.post(f"{url}/declineChatJoinRequest", json={
                    "chat_id": chat_id,
                    "user_id": user_id,
                })
                if res.json().get("ok"):
                    print(f"Отклонён: {user_id}")
                    declined += 1
                time.sleep(0.3)

    print(f"Итого отклонено: {declined}")

while True:
    decline_all()
    time.sleep(2)
