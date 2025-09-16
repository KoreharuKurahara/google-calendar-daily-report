def load_color_settings(path='color-settings.json'):
    import json
    with open(path, encoding='utf-8') as f:
        return json.load(f)

import os
from datetime import datetime, timedelta
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_events_for_date_selected(service, date_str, calendar_ids):
    # date_str: 'YYYY-MM-DD'
    date = datetime.strptime(date_str, '%Y-%m-%d')
    time_min = date.strftime('%Y-%m-%dT00:00:00Z')
    time_max = (date + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z')
    all_events = []
    for cal_id in calendar_ids:
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        for event in events_result.get('items', []):
            event['calendarId'] = cal_id
            all_events.append(event)
    return all_events


def post_to_slack(message, channel=None):
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    channel = channel or os.getenv('SLACK_CHANNEL_ID')
    client = WebClient(token=slack_token)
    try:
        response = client.chat_postMessage(channel=channel, text=message)
        print("Slack投稿成功:", response["ts"])
    except SlackApiError as e:
        print("Slack投稿失敗:", e.response["error"])
# 例: 日報本文を作成したら
# post_to_slack(report_text)


# --- 共通処理 ---
def get_google_service():
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    import boto3
    import base64
    TOKEN_PATH = 'token.json'
    creds = None
    # Lambda環境判定: AWS_LAMBDA_FUNCTION_NAMEが環境変数にあればLambda
    is_lambda = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
    credentials_json = None
    if is_lambda:
        # Secrets Managerから取得
        secret_name = os.getenv('GOOGLE_CREDENTIALS_SECRET_NAME', 'kurahara-google-calendar-daily-report-credentials')
        region_name = os.getenv('AWS_REGION', 'ap-northeast-1')
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in get_secret_value_response:
            credentials_json = get_secret_value_response['SecretString']
        else:
            credentials_json = base64.b64decode(get_secret_value_response['SecretBinary']).decode('utf-8')
        credentials_path = '/tmp/credentials.json'
        with open(credentials_path, 'w') as f:
            f.write(credentials_json)
        credentials_file = credentials_path
    else:
        credentials_file = 'credentials.json'
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_calendar_ids():
    private_calendar_id = os.getenv('PRIVATE_CALENDAR_ID')
    public_calendar_id = os.getenv('PUBLIC_CALENDAR_ID')
    calendar_ids = []
    if private_calendar_id:
        calendar_ids.append(private_calendar_id)
    if public_calendar_id:
        calendar_ids.append(public_calendar_id)
    return calendar_ids

def generate_and_post_report(date_str, service=None):
    try:
        if service is None:
            service = get_google_service()
        calendar_ids = get_calendar_ids()
        events = get_events_for_date_selected(service, date_str, calendar_ids)
        color_settings = load_color_settings()
        if not events:
            msg = f"{date_str} の予定はありません。"
            print(msg)
            post_to_slack(msg)
            return
        colorname_duration = {}
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            duration = (end_dt - start_dt).total_seconds() / 60 / 60
            color_id = event.get('colorId', '0')
            color_name = color_settings.get(str(color_id), f'color_{color_id}')
            event_type = event.get('eventType', 'default')
            if event_type == 'default':
                colorname_duration[color_name] = colorname_duration.get(color_name, 0) + duration
        report = f"{date_str} の実績（時間）: {colorname_duration}"
        print(report)
        post_to_slack(f"今日もお疲れ様でした！　一旦手を止めて、{date_str} の作業工数を振り返りましょう")
        post_to_slack(report)
    except Exception as e:
        print(f"エラー発生: {e}")
        post_to_slack(f"日報生成・投稿時にエラー: {e}")

# Lambdaエントリポイント
def lambda_handler(event, context):
    # 日付は event["date"] または Lambda起動日（UTC）
    date_str = event.get("date") if event and "date" in event else datetime.utcnow().strftime('%Y-%m-%d')
    generate_and_post_report(date_str)
    return {"statusCode": 200, "body": f"Report for {date_str} posted."}

if __name__ == "__main__":
    # 日付指定（コマンドライン引数 or 今日）
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
    generate_and_post_report(date_str)
