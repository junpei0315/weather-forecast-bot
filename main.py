from fastapi import FastAPI, Request, Header, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
import requests



from datetime import datetime
import xml.etree.ElementTree as ET

def parse_weather(xml_string: str, max_entries: int =10) -> str:
    ns = {'ydf': 'http://olp.yahooapis.jp/ydf/1.0'}
    root = ET.fromstring(xml_string)
    location_name = root.find('.//ydf:Name', ns).text
    weathers = root.find('.//ydf:WeatherList', ns)

    seen_hours = set()
    output = [f"🗾 地点情報: {location_name}\n"]
    count = 0

    for weather in weathers.findall('ydf:Weather', ns):
        if count >=max_entries:
            break
        weather_type_en = weather.find('ydf:Type', ns).text
        date_str = weather.find('ydf:Date', ns).text
        dt = datetime.strptime(date_str, "%Y%m%d%H%M")
        hour_key = dt.strftime("%Y%m%d%H")
        if hour_key in seen_hours:
            continue
        seen_hours.add(hour_key)

        weather_type_jp = "観測値" if weather_type_en == "observation" else "予報値"
        date_jp = dt.strftime("%Y年%m月%d日 %H時%M分")
        rainfall = weather.find('ydf:Rainfall', ns).text

        output.append(f"📅 {date_jp} 時点（{weather_type_jp}）: 降水量 {rainfall} mm")
        count += 1
        if count ==0:
            output.append("データが取得できませんでした。")

    return "\n".join(output)

# .env ファイルの読み込み
load_dotenv()

# 環境変数から取得
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

weather_api_url="https://map.yahooapis.jp/weather/V1/place"
CLIENT_ID= os.getenv("CLIENT_ID")

payload = {
            "appid": CLIENT_ID,
           "coordinates": "135.5685,34.8163"
           }

r = requests.get(weather_api_url,params=payload)
print(r.text)


# LINE SDK のセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


app = FastAPI()

@app.get("/weather")
def getWeather():
    r = requests.get(weather_api_url,params=payload)
    return r.text

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

    if msg == "天気":
        r = requests.get(weather_api_url, params=payload)
        xml_string = r.text
        reply = parse_weather(r.text, max_entries=10)
    elif msg == "おはよう":
        reply = "おはよう！"
    else:
        reply = "「おはよう」か「天気」と言ってみてね！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
