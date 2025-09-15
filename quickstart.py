import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES)  # credentials.jsonはGoogle CloudでDLしたファイル
creds = flow.run_local_server(port=8080)

service = build('calendar', 'v3', credentials=creds)
events_result = service.events().list(calendarId='primary', maxResults=10).execute()
events = events_result.get('items', [])

for event in events:
    print(event['summary'], event['start'].get('dateTime', event['start'].get('date')))