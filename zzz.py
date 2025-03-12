import os
import base64
import google.auth
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
import json

# 🔹 Gmail API のスコープ（メール送信のみ）
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# 🔹 OAuth 2.0 認証を行い、トークンを取得
def get_credentials():
    creds = None


def get_credentials():
    creds = None

    # # 🔹 以前の認証情報（token.json）があればロード
    # if os.path.exists("token.json"):
    #     creds = google.auth.load_credentials_from_file("token.json")[0]
        

    # # 🔹 認証が無効（期限切れ・なし）の場合、新規認証
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             "client_secret_845610956511-ej3htjkbtukko0sfff2979837ab83elh.apps.googleusercontent.com.json", 
    #             SCOPES,
    #             redirect_uri="http://localhost:8080/oauth2callback")
    #         creds = flow.run_local_server(port=8080)

    #     # 🔹 新しいトークンを保存
    #     with open("token.json", "w") as token:
    #         token.write(creds.to_json())

    # return creds


    # # 🔹 以前の認証情報があるか確認
    if os.path.exists("token.json"):
        try:
            with open("token.json", "r") as token_file:
                data = json.load(token_file)
                
                # 🔹 refresh_token が欠落している場合は削除
                if "refresh_token" not in data:
                    print("⚠️ refresh_token がないため、再認証が必要です。")
                    os.remove("token.json")
                    creds = None
                else:
                    creds = google.auth.load_credentials_from_file("token.json")[0]
        except Exception as e:
            print(f"⚠️ token.json の読み込みに失敗: {e}")
            os.remove("token.json")
            creds = None

    # 🔹 認証が無効（期限切れ・なし）の場合、新規認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret_845610956511-ej3htjkbtukko0sfff2979837ab83elh.apps.googleusercontent.com.json", 
                SCOPES,
                redirect_uri="http://localhost:8080/oauth2callback"
            )
            creds = flow.run_local_server(port=8080)  # 🔹 ローカルブラウザで認証


        # 🔹 新しいトークンを保存（refresh_token を確実に保存）
        with open("token.json", "w") as token_file:
            json.dump({
                "type": "authorized_user",
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes
            }, token_file, indent=4)

    return creds

# 🔹 メールを送信
def send_email(to_email, subject, body):
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    # 🔹 メールの作成
    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # 🔹 Gmail API を使って送信
    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print("✅ Email sent successfully!")
    except Exception as e:
        print("❌ Error:", e)

# 🔹 メール送信のテスト
if __name__ == "__main__":
    print("start")
    send_email("wendover42@gmail.com", "Test Email", "This is a test email from Python using OAuth 2.0.")
