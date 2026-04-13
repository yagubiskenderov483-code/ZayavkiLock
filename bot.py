import asyncio
import requests
import time
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetChatInviteRequestsRequest, HideChatJoinRequestRequest
from telethon.tl.types import InputPeerChannel

API_ID       = 28687552
API_HASH     = "1abf9a58d0c22f62437bec89bd6b27a3"
BOT_TOKEN = "8631457299:AAGpZIld3nTruS4xgpWWflo1oMayajl74dI"
OWNER_ID  = 8493646452
GROUP_USERNAME = "username_группы"  # без @

bot_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
group_id = None

def send_message(chat_id, text):
    requests.post(f"{bot_url}/sendMessage", json={"chat_id": chat_id, "text": text})

async def decline_all_old(client, chat_id):
    entity = await client.get_entity(GROUP_USERNAME)
    peer   = InputPeerChannel(entity.id, entity.access_hash)

    declined = 0
    while True:
        result = await client(GetChatInviteRequestsRequest(
            peer=peer,
            limit=100,
            offset_date=None,
            offset_user=None,
        ))
        if not result.users:
            break

        for user in result.users:
            await client(HideChatJoinRequestRequest(
                peer=peer,
                user_id=user.id,
                approved=False,
            ))
            print(f"Отклонён: {user.id}")
            declined += 1
            await asyncio.sleep(0.3)

    send_message(chat_id, f"✅ Отклонено всего заявок: {declined}")

async def main():
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start()

    offset = None
    while True:
        try:
            params = {
                "timeout": 10,
                "allowed_updates": ["message", "chat_join_request"],
            }
            if offset:
                params["offset"] = offset

            r = requests.get(f"{bot_url}/getUpdates", params=params)
            updates = r.json().get("result", [])

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
                        send_message(chat_id, "👋 Привет!\n/decline — удалить ВСЕ заявки включая старые")

                    elif text == "/decline":
                        send_message(chat_id, "⏳ Удаляю все заявки включая старые...")
                        await decline_all_old(client, chat_id)

                if "chat_join_request" in update:
                    uid     = update["chat_join_request"]["from"]["id"]
                    gid     = update["chat_join_request"]["chat"]["id"]
                    name    = update["chat_join_request"]["from"].get("first_name", "—")
                    res = requests.post(f"{bot_url}/declineChatJoinRequest", json={
                        "chat_id": gid,
                        "user_id": uid,
                    })
                    if res.json().get("ok"):
                        print(f"Авто-отклонён: {name} ({uid})")

            await asyncio.sleep(2)
        except Exception as e:
            print("Ошибка:", e)
            await asyncio.sleep(5)

asyncio.run(main())
