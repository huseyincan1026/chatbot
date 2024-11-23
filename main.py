import os
import sys
import httpx
from bs4 import BeautifulSoup
from fastapi import Request, FastAPI, HTTPException
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import FlexSendMessage  # Bu satır eklendi

# Kanal sırrı ve kanal erişim token'ını çevresel değişkenlerden alıyoruz
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('LINE_CHANNEL_SECRET çevresel değişkenini belirtin.')
    sys.exit(1)
if channel_access_token is None:
    print('LINE_CHANNEL_ACCESS_TOKEN çevresel değişkenini belirtin.')
    sys.exit(1)

configuration = Configuration(
    access_token=channel_access_token
)

app = FastAPI()
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)

# Haberleri çekmek için asenkron fonksiyon
async def get_news():
    url = 'https://newsapi.org/v2/top-headlines'  # News API endpoint
    params = {
        'sources': 'bbc-news',  # BBC News kaynağını kullanıyoruz
        'apiKey': '0d768d83e4e74f1b9bfc7ea82c967b75',  # API anahtarınızı buraya ekleyin
        'pageSize': 10  # 10 haber alıyoruz
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    data = response.json()

    # Haber başlıkları, içerikler ve görselleri alıyoruz
    headlines = []
    links = []
    image_urls = []
    contents = []

    for article in data['articles']:
        headlines.append(article['title'])
        links.append(article['url'])
        image_urls.append(article['urlToImage'])

        # Her bir haberin içeriğini çekiyoruz
        async with httpx.AsyncClient() as client:
            r = await client.get(article['url'])
        soup = BeautifulSoup(r.text, 'lxml')

        content = soup.findAll('div', {'data-component': 'text-block'})
        article_text = ""
        for i in content:
            article_text += i.get_text() + "\n"

        contents.append(article_text)

    return headlines, links, image_urls, contents

@app.get("/")
async def read_root():
    return {"message": "LINE bot'a hoş geldiniz!"}

@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Geçersiz imza")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue

        # Haber başlıklarını alıyoruz
        headlines, links, image_urls, contents = await get_news()

        # Başlıkları liste olarak göndermek
        buttons = []
        for i, headline in enumerate(headlines):
            buttons.append({
                "type": "message",
                "label": headline,
                "text": f"Seçilen haber: {i}",  # Seçilen haberin index değeri
                "data": str(i)  # Index'i veri olarak gönderiyoruz
            })

        # FlexMessage ile başlıkları göndermek
        flex_message = {
            "type": "carousel",
            "contents": [{
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [{
                        "type": "button",
                        "action": button
                    } for button in
