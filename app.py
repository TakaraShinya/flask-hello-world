import os
import sys
from flask import Flask, request, abort
import base64
import hashlib
import hmac
import json
import datetime
import requests
from dotenv import load_dotenv

from linebot import (
    WebhookHandler,
    WebhookParser,
    LineBotApi
)
from linebot.models.events import (
    MessageEvent,
    FollowEvent,
    UnfollowEvent,
    JoinEvent,
    LeaveEvent,
    PostbackEvent,
    BeaconEvent,
    AccountLinkEvent,
    MemberJoinedEvent,
    MemberLeftEvent,
    ThingsEvent,
    UnsendEvent,
    VideoPlayCompleteEvent,
    UnknownEvent,
)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage)

app = Flask(__name__)
app.debug = False
load_dotenv(override=True)
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
handler = WebhookHandler(channel_secret)
parser = WebhookParser(channel_secret)

@app.route("/")
def healthcheck():
    return "It works!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    app.logger.info(signature.encode('utf-8'))

    hash = hmac.new(channel_secret.encode('utf-8'),
        body.encode('utf-8'), hashlib.sha256).digest()
    encode_signature = base64.b64encode(hash)
    app.logger.info(encode_signature)

    # handle webhook body
    # try:
        # handler.handle(body, signature)
    # events = parser.parse(body, signature)
    # except InvalidSignatureError:
        # app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        # abort(400)

    body_json = json.loads(body)
    events = []
    for event in body_json['events']:
        event_type = event['type']
        if event_type == 'message':
            events.append(MessageEvent.new_from_json_dict(event,
                            use_raw_message=False))
        elif event_type == 'follow':
            events.append(FollowEvent.new_from_json_dict(event))
        elif event_type == 'unfollow':
            events.append(UnfollowEvent.new_from_json_dict(event))
        elif event_type == 'join':
            events.append(JoinEvent.new_from_json_dict(event))
        elif event_type == 'leave':
            events.append(LeaveEvent.new_from_json_dict(event))
        elif event_type == 'postback':
            events.append(PostbackEvent.new_from_json_dict(event))
        elif event_type == 'beacon':
            events.append(BeaconEvent.new_from_json_dict(event))
        elif event_type == 'accountLink':
            events.append(AccountLinkEvent.new_from_json_dict(event))
        elif event_type == 'memberJoined':
            events.append(MemberJoinedEvent.new_from_json_dict(event))
        elif event_type == 'memberLeft':
            events.append(MemberLeftEvent.new_from_json_dict(event))
        elif event_type == 'things':
            events.append(ThingsEvent.new_from_json_dict(event))
        elif event_type == 'unsend':
            events.append(UnsendEvent.new_from_json_dict(event))
        elif event_type == 'videoPlayComplete':
            events.append(VideoPlayCompleteEvent.new_from_json_dict(event))
        else:
            LOGGER.info('Unknown event type. type=' + event_type)
            events.append(UnknownEvent.new_from_json_dict(event))

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        app.logger.info("event.message.text: " + event.message.text)
        if not isinstance(event, MessageEvent):
            app.logger.info("not isinstance(event, MessageEvent): ")
            continue
        app.logger.info("event.reply_token: " + event.reply_token)
        line_bot_api = LineBotApi(os.getenv('LINE_ACCESS_TOKEN'))
        if event.message.text == '現在時刻':
            reply_message = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%Sです')
            line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_message))

        elif event.message.text == '天気':

            city_code = "471010" 
            url = "https://weather.tsukumijima.net/api/forecast/city/" + city_code

            try:
                response = requests.get(url)
                response.raise_for_status()     # ステータスコード200番台以外は例外とする
            except requests.exceptions.RequestException as e:
                print("Error:{}".format(e))

            else:
                weather_json = response.json()
                print(weather_json['forecasts'][0]['chanceOfRain']) # 0:今日 1:明日 2:明後日
                kyou = "今日：" + weather_json['forecasts'][0]['image']['title']
                asita = "明日：" + weather_json['forecasts'][1]['image']['title']
                asatte = "明後日:" + weather_json['forecasts'][2]['image']['title']    
            line_bot_api.reply_message(
                            event.reply_token,
                          TextSendMessage(text=kyou+"\n"+asita+"\n" +asatte)) 
        elif event.message.text == '時間割':
            test1 = "月曜日:音国国算社\n火曜日:算理理算国\n水曜日:国国算図理総\n木曜日:体体社算国\n金曜日:道理算体国総"

            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=test1+"\n "))
        else:
            line_bot_api.reply_message(
                            event.reply_token,
                        TextSendMessage(text=event.message.text))  
    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("5000"), debug=True)
