from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import re
import threading

app = Flask(__name__)

# LINE Bot設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 既存の変換ロジックをインポート/統合
def convert_music(url):
    """既存の自宅PC変換エンジンを呼び出す"""
    # ここに現在のconvert関数のロジックを統合
    # 同じdownloadsフォルダに保存
    try:
        # 既存の変換処理を実行
        result = your_existing_conversion_function(url)
        return {
            'success': True,
            'title': result.get('title', 'Unknown'),
            'filename': result.get('filename', 'Unknown'),
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url': url
        }

# URL検出関数（シンプル版）
def extract_urls(text):
    """テキストからURLを抽出"""
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    return urls

# LINE Webhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({"error": "Invalid signature"}), 400
    
    return 'OK'

# LINEメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    urls = extract_urls(user_message)
    
    if urls:
        # 変換開始メッセージ
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="🎵 音楽変換を開始します...\nしばらくお待ちください")
        )
        
        # バックグラウンドで変換処理
        threading.Thread(
            target=process_conversion_batch,
            args=(event.source.user_id, urls)
        ).start()
    else:
        # URLがない場合のガイドメッセージ
        help_text = """🎵 音楽変換Botの使い方

変換したい動画のURLを貼り付けてください

対応サイト例:
• YouTube
• SoundCloud  
• Twitter/X
• TikTok
• ニコニコ動画

例: https://youtube.com/watch?v=..."""
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )

def process_conversion_batch(user_id, urls):
    """複数URLを順次変換"""
    for i, url in enumerate(urls):
        try:
            # 進捗通知（複数URLの場合）
            if len(urls) > 1:
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=f"🔧 {i+1}/{len(urls)}件目を変換中...")
                )
            
            # 変換実行
            result = convert_music(url)
            
            # 結果通知
            if result['success']:
                message = f"✅ 変換完了!\n📝 タイトル: {result['title']}\n💾 ファイル: {result['filename']}"
            else:
                message = f"❌ 変換失敗\n🔗 URL: {result['url']}\n📛 理由: {result['error']}"
                
        except Exception as e:
            message = f"❌ エラー発生\n🔗 URL: {url}\n📛 詳細: {str(e)}"
        
        # 結果を送信
        line_bot_api.push_message(user_id, TextSendMessage(text=message))

# 既存のRailway互換エンドポイント（必要に応じて）
@app.route('/convert', methods=['POST'])
def convert_api():
    """既存システムとの互換性を維持"""
    data = request.get_json()
    url = data.get('url')
    
    if url:
        result = convert_music(url)
        return jsonify(result)
    return jsonify({'error': 'URL required'}), 400

# ヘルスチェック
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Music Converter Hybrid Server'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
