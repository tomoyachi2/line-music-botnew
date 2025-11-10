from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yt_dlp
import os
import threading
import tempfile

app = Flask(__name__)

# 環境変数から取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 一時ディレクトリを作成
os.makedirs('/tmp/downloads', exist_ok=True)

def download_youtube_audio(song_name, user_id):
    try:
        print(f"🎵 処理開始: {song_name}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '/tmp/downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False
        }
        
        search_query = f"ytsearch1:{song_name}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            title = info.get('title', '不明な曲')
            
            success_message = f"""
✅ 変換完了！
曲名: {title}
MP3をサーバーに保存しました！

次の曲をお楽しみください！🎵
            """
            
            # ユーザーに通知
            line_bot_api.push_message(user_id, TextSendMessage(text=success_message))
            print(f"✅ 完了: {title}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        error_message = f"""
❌ エラーが発生しました

考えられる原因:
• 曲名が正しくない
• ネットワークエラー
• 動画が非公開

別の曲名でお試しください！
        """
        line_bot_api.push_message(user_id, TextSendMessage(text=error_message))

@app.route("/")
def home():
    return "🎵 音楽変換Botが稼働中です！"

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
    
    # 即時返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"「{user_message}」を検索中...🔍")
    )
    
    # 別スレッドで変換処理
    thread = threading.Thread(
        target=download_youtube_audio, 
        args=(user_message, user_id)
    )
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
