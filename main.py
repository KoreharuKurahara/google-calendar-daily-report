import json
def load_color_settings(path='color-settings.json'):
    with open(path, encoding='utf-8') as f:
        return json.load(f)
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

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

if __name__ == "__main__":
    # 認証
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    SERVICE_ACCOUNT_FILE = 'serviceaccount-credentials.json'  # Lambdaなら環境変数やSecrets Manager経由で取得

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('calendar', 'v3', credentials=credentials)
    # flow = InstalledAppFlow.from_client_secrets_file(
    #     'credentials.json', SCOPES)
    # creds = flow.run_local_server(port=8080)
    # service = build('calendar', 'v3', credentials=creds)

    # 日付指定（例: コマンドライン引数 or 入力）
    import sys
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = input('日付をYYYY-MM-DD形式で入力してください: ')

    # .envからPRIVATE_CALENDAR_IDを取得
    private_calendar_id = os.getenv('PRIVATE_CALENDAR_ID')
    public_calendar_id = os.getenv('PUBLIC_CALENDAR_ID')
    calendar_ids = []
    if private_calendar_id:
        calendar_ids.append(private_calendar_id)
    if public_calendar_id:
        calendar_ids.append(public_calendar_id)
    events = get_events_for_date_selected(service, date_str, calendar_ids)
    print("今日もお疲れ様でした！　一旦手を止めて、今日の作業工数を振り返りましょう")
    post_to_slack(f"今日もお疲れ様でした！　一旦手を止めて、{date_str} の作業工数を振り返りましょう")

    # color-settings.jsonの読み込み
    color_settings = load_color_settings()
    if not events:
        print(f"{date_str} の予定はありません。")
    else:
        print(f"{date_str} の実績（時間）:")
        colorname_duration = {}
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            # 時間計算のため datetime オブジェクトに変換
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            duration = (end_dt - start_dt).total_seconds() / 60 / 60  # 時間単位
            summary = event.get('summary', '(タイトルなし)')
            color_id = event.get('colorId', '0')
            color_name = color_settings.get(str(color_id), f'color_{color_id}')
            cal_id = event.get('calendarId', '')
            event_type = event.get('eventType', 'default')
            print(f"- {start} ～ {end} ({duration:.0f}分) : {summary} [Color: {color_name}] [Calendar: {cal_id}] [EventType: {event_type}]")
        # color名ごとに集計（EventTypeがdefaultのもののみ）
            if event_type == 'default':
                colorname_duration[color_name] = colorname_duration.get(color_name, 0) + duration        
        print(colorname_duration)
        post_to_slack(f"{date_str} の実績（時間）: {colorname_duration}")
