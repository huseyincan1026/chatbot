import os
import sys
import requests
from bs4 import BeautifulSoup
from fastapi import Request, FastAPI, HTTPException
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
AsyncApiClient,
AsyncMessagingApi,
Configuration,
ReplyMessageRequest,
TextMessage
)
from linebot.v3.messaging import ImageMessage
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent



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


# Haberleri çekmek için fonksiyon

def get_news():
url = 'https://newsapi.org/v2/top-headlines'  # News API endpoint
params = {
    'sources': 'bbc-news',  # BBC News kaynağını kullanıyoruz
    'apiKey': '0d768d83e4e74f1b9bfc7ea82c967b75',  # API anahtarınızı buraya ekleyin
    'pageSize': 5  # 5 haber alıyoruz
}

response = requests.get(url, params=params)
data = response.json()

article_title = data['articles'][0]['title']
article_image_url = data['articles'][0]['urlToImage']

links = []
for link in data['articles']:
    links.append(link['url'])

# İlk haberin içeriğini çekiyoruz
r = requests.get(links[0])
soup = BeautifulSoup(r.text, 'lxml')

# Haber içeriğini alıyoruz
content = soup.findAll('div', {'data-component': 'text-block'})
article_text = ""
for i in content: 
    article_text += i.get_text() + "\n"

return article_text, article_image_url, article_title

@app.get("/")
async def read_root():
return {"message": "LINE bot'a hoş geldiniz!"}


from linebot.v3.messaging import ImageMessage

@app.post("/callback")
async def handle_callback(request: Request):
signature = request.headers['X-Line-Signature']

# Request gövdesini metin olarak alıyoruz
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

    # Kullanıcı mesaj gönderdiğinde haber içeriğini, başlık ve görseli alıyoruz
    news_content, article_image_url, article_title = get_news()

    # Başlık, resim ve haber içeriğini tek bir reply_message ile gönderiyoruz
    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text=f"{article_title}"),
                ImageMessage(
                    original_content_url=article_image_url,  # Resmin tam boyutlu URL'si
                    preview_image_url=article_image_url  # Resmin küçük boyutlu önizlemesi
                ),
                TextMessage(text=f"İşte son haber:\n{news_content}")
            ]
        )
    )

return 'OK'


