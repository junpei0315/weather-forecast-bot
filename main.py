from fastapi import FastAPI, Request, Header, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
import requests

# .env ファイルの読み込み
load_dotenv()

# 環境変数から取得
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

weather_api_url="https://map.yahooapis.jp/weather/V1/place"
CLIENT_ID= os.getenv("CLIENT_ID")

payload = {"appid":"client_ID",
           "coordinates": "34.8163,135.5685"}

r = requests.get(weather_api_url,params=payload)
print(r.text)


# LINE SDK のセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


app = FastAPI()

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"あなたのメッセージ: {user_message}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
#仮想環境に入ってね：Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# .\venv\Scripts\activate
# uvicorn main:app --reload
# uvicorn main:app --host   
#pip install fastapi uvicorn python-dotenv requests
# pip install line-bot-sdk
@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == "おはよう":
        reply = "おはよう！"
    else:
        reply = "「おはよう」と言ってみてね！"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
    