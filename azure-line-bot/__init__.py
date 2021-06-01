import logging
import os
import azure.functions as func

## https://docs.microsoft.com/ja-jp/azure/cognitive-services/luis/client-libraries-rest-api?tabs=windows&pivots=programming-language-python
from azure.cognitiveservices.language.luis.authoring import LUISAuthoringClient
from azure.cognitiveservices.language.luis.authoring.models import ApplicationCreateObject
from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient
from msrest.authentication import CognitiveServicesCredentials
from functools import reduce

import json, time, uuid

appId = os.getenv('APP_ID', None)
predictionKey = os.getenv('PREDICTION_KEY', None)
predictionEndpoint = os.getenv('PREDICTION_ENDPOINT', None)

runtimeCredentials = CognitiveServicesCredentials(predictionKey)
clientRuntime = LUISRuntimeClient(endpoint=predictionEndpoint, credentials=runtimeCredentials)

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # get x-line-signature header value
    signature = req.headers['x-line-signature']

    # get request body as text
    body = req.get_body().decode("utf-8")
    logging.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        func.HttpResponse(status_code=400)

    return func.HttpResponse('OK')


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    predictionRequest = { "query" : event.message.text }
    predictionResponse = clientRuntime.prediction.get_slot_prediction(appId, "production", predictionRequest)
    logging.info("Top intent: {}".format(predictionResponse.prediction.top_intent))
    logging.info("Sentiment: {}".format (predictionResponse.prediction.sentiment))
    logging.info("Intents: ")
    for intent in predictionResponse.prediction.intents:
        logging.info("\t{}".format (json.dumps (intent)))
        logging.info("\t{}".format (type(intent)))
    logging.info("Entities: {}".format (predictionResponse.prediction.entities))
    line_bot_api.reply_message(
        event.reply_token,
        [TextSendMessage(text=f'Intent: {predictionResponse.prediction.top_intent}'),
         TextSendMessage(text=f'Entity: {predictionResponse.prediction.entities}')]
    )
