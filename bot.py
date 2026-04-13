import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = int(os.getenv("CHAT_ID"))

def decline_all():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    declined = 0

    while True:
        r = requests.get(f"{url}/getChatJoinRequests", params={"chat_id": CHAT_ID, "limit": 100})
        data = r.json()

        if not data.get("ok") or not data["result"]:
            break

        for req in data["result"]:
            user_id = req["from"]["id"]
            requests.post(f"{url}/declineChatJoinRequest", json={
                "chat_id": CHAT_ID,
                "user_id": user_id,
            })
            print(f"Отклонён: {user_id}")
            declined += 1
            time.sleep(0.3)

    print(f"Готово. Отклонено: {declined}")

decline_all()
