from fastapi import FastAPI, Request
from line_bot_sdk import LineBotApi, WebhookHandler
from line_bot_sdk.models import MessageEvent, TextMessage, PostbackEvent

app = FastAPI()

# LINE bot bilgilerinizi burada doldurun
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.post("/callback")
async def callback(request: Request):
    body = await request.body()
    signature = request.headers["X-Line-Signature"]
    handler.handle(body.decode(), signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Kullanıcıya seçenekleri sunma
    buttons_template = TemplateSendMessage(
        alt_text="Please choose",
        template=ButtonsTemplate(
            text="Choose an option:",
            actions=[
                PostbackAction(label="Option 1", data="option1"),
                PostbackAction(label="Option 2", data="option2"),
                PostbackAction(label="Option 3", data="option3")
            ]
        )
    )
    line_bot_api.reply_message(event.reply_token, buttons_template)

@handler.add(PostbackEvent)
def handle_postback(event):
    # Kullanıcının seçimine göre mesaj gönder
    if event.postback.data == "option1":
        line_bot_api.reply_message(event.reply_token, TextMessage(text="You chose option 1"))
    elif event.postback.data == "option2":
        line_bot_api.reply_message(event.reply_token, TextMessage(text="You chose option 2"))
    elif event.postback.data == "option3":
        line_bot_api.reply_message(event.reply_token, TextMessage(text="You chose option 3"))
