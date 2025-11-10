@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id
    
    # ユーザーIDをコンソールに表示（重要！）
    print(f"🔍 ユーザーID: {user_id}")
    print(f"📝 メッセージ: {user_message}")
    
    # 即時返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🎵 「{user_message}」リクエストを受信しました！")
    )
    
    # テスト通知（兄さん自身に送信）
    try:
        test_message = f"""
📋 テスト通知
あなたのユーザーID: {user_id}
このIDをBROTHER_USER_IDに設定してください
        """
        line_bot_api.push_message(user_id, TextSendMessage(text=test_message))
    except Exception as e:
        print(f"❌ 通知エラー: {e}")
