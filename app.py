from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os
from datetime import datetime

app = Flask(__name__)

# 環境変数から取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ⚠️ ここは後で実際のユーザーIDに変更
BROTHER_USER_ID = "あなたのユーザーID"

@app.route("/")
def home():
    return "🎵 音楽リクエストBot (通知専用)"

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
    
    # ユーザーIDをログに出力（重要！）
    print(f"🔍 ユーザーID: {user_id}")
    print(f"📝 メッセージ: {user_message}")
    
    # 即時返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🎵 「{user_message}」リクエストを受信しました！")
    )
    
    # 自宅パソコンに転送を試みる
    try:
        response = requests.post(
            "http://192.168.0.101:5000/process",  # あなたのパソコンIP
            json={
                'song_name': user_message, 
                'user_id': user_id
            },
            timeout=3
        )
        
        if response.status_code == 200:
            line_bot_api.push_message(
                user_id, 
                TextSendMessage(text="✅ 自宅パソコンで処理を開始しました！")
            )
        else:
            raise Exception("パソコンに接続できません")
            
    except Exception as e:
        # パソコンがオフライン → 兄さんに通知
        offline_message = f"""
❌ 自宅パソコンがオフラインです

リクエスト: {user_message}
時間: {datetime.now().strftime('%H:%M')}

パソコンを起動してください！
        """
        
        print(f"📋 兄さんに通知: {offline_message}")
        
        # 妹さんに通知
        line_bot_api.push_message(
            user_id, 
            TextSendMessage(text="📋 兄さんにリクエストを通知しました！")
        )

@app.route("/notify", methods=['POST'])
def handle_notification():
    """自宅パソコンからの通知を受信"""
    try:
        data = request.json
        user_id = data['user_id']
        message = data['message']
        
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"通知エラー: {e}")
        return jsonify({'status': 'error'})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 通知Botを起動しました！ポート: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
