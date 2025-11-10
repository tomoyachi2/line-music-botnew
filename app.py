from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# 環境変数から取得（後で設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "🎵 Music Bot is Running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id
    
    # まず即時返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"「{user_message}」を受信しました！🎵")
    )
    
    # あなたのパソコンにリクエストを転送（試行）
    try:
        # 注意: ここは後であなたのパソコンのURLに変更
        response = requests.post(
            "http://192.168.0.101:5000/process",
            json={'song_name': user_message, 'user_id': user_id},
            timeout=3
        )
        
        if response.status_code == 200:
            line_bot_api.push_message(
                user_id, 
                TextSendMessage(text="✅ パソコンで処理を開始しました！数分お待ちください...")
            )
        else:
            raise Exception("パソコンに接続できません")
            
    except Exception as e:
        # パソコンがオフラインの場合
        offline_message = """
❌ 現在、変換サーバーがオフラインです

【対処方法】
1. 兄さんのパソコンを起動してください
2. パソコンで変換プログラムを起動してください
3. 起動後、再度同じ曲名を送信してください

パソコンが起動すると自動で処理を開始します！
        """
        line_bot_api.push_message(user_id, TextSendMessage(text=offline_message))

@app.route("/notify", methods=['POST'])
def handle_notification():
    """パソコンからの完了通知を受信"""
    try:
        data = request.json
        user_id = data['user_id']
        message = data['message']
        
        # ユーザーに結果を通知
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"通知エラー: {e}")
        return jsonify({'status': 'error'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
