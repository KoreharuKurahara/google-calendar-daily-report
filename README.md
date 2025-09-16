
# google-calendar-daily-report

Googleカレンダーの予定から作業工数を自動集計し、Slackに日報として投稿するPythonアプリケーションです。

## 主な特徴
- GoogleカレンダーAPIから複数カレンダー（PRIVATE/PUBLIC）予定を取得
- 予定の色（colorId）を日本語名に変換し、色ごとに工数を集計
- Slack APIで日報を自動投稿
- AWS Lambda/ローカル両対応、トークン自動管理

## セットアップ
1. Python 3.8以上、仮想環境推奨
2. 必要パッケージ
	```sh
	pip install -r requirements.txt
	# または
	pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib slack_sdk python-dotenv
	```
3. `.env`ファイル例（ローカル用）
	```env
	GOOGLE_CLIENT_ID=...
	GOOGLE_CLIENT_SECRET=...
	GOOGLE_REDIRECT_URI=http://localhost:8080/
	PUBLIC_CALENDAR_ID=xxx@group.calendar.google.com
	PRIVATE_CALENDAR_ID=yyy@group.calendar.google.com
	SLACK_BOT_TOKEN=xoxb-...
	SLACK_CHANNEL_ID=Cxxxxxxx
	AWS_PROFILE=your-aws-profile
	AWS_REGION=ap-northeast-1
	GOOGLE_CREDENTIALS_SECRET_NAME=kurahara-google-calendar-daily-report-credentials
	GOOGLE_TOKEN_SECRET_NAME=kurahara-google-calendar-daily-report-token
	```
4. `color-settings.json`でcolorId→日本語名変換を定義
5. Google CloudでOAuth認証情報を作成し、初回のみ手動認証→`token.json`保存
	- ローカルで`python lambda_function.py`を実行し、認証フローを完了させて`token.json`を生成
	- `credentials.json`と`token.json`はAWS Secrets Managerに登録（Lambda用）

## 使い方
```sh
python lambda_function.py 2025-09-15
```
指定日付の予定を取得し、色ごとに工数を集計してSlackに投稿します。

## Google認証について
- 初回のみ認証画面が表示されます。以降は`token.json`のrefresh_tokenで自動更新されます。
- サービスアカウント方式は組織の制限やカレンダー共有権限に注意してください。

## Slack連携
- Slack Appを作成しBot Tokenを取得、投稿先チャンネルにBotを招待してください。

## カレンダーIDの指定
- `.env`の`PRIVATE_CALENDAR_ID`と`PUBLIC_CALENDAR_ID`に対象カレンダーIDを設定

## 色設定
- `color-settings.json`でcolorIdごとの分類名を自由に編集可能


## Lambda運用・デプロイ
- AWS Lambdaでの定期実行も可能。Secrets Managerや環境変数で認証情報を安全に管理してください。
- Lambda用のSecrets Manager登録例：
	- `kurahara-google-calendar-daily-report-credentials`（credentials.jsonの内容）
	- `kurahara-google-calendar-daily-report-token`（token.jsonの内容）
- Lambdaの環境変数に以下を設定
	- `GOOGLE_CREDENTIALS_SECRET_NAME`、`GOOGLE_TOKEN_SECRET_NAME`、`PUBLIC_CALENDAR_ID`、`PRIVATE_CALENDAR_ID`、`SLACK_BOT_TOKEN`、`SLACK_CHANNEL_ID`、`AWS_REGION`
- Lambdaのハンドラは`lambda_function.lambda_handler`に設定
- Lambda実行ロールにはSecrets ManagerのGetSecretValue権限が必要
- デプロイは`deploy.sh`でzip化し、認証情報ファイルはzipに含めないこと（セキュリティ上必須）

---

---

### セキュリティ注意
- `credentials.json`や`token.json`は絶対にリポジトリやデプロイzipに含めないこと
- Secrets Manager運用を徹底

---

詳細な要件・設計・タスク分解は`docs/requirement.md` `docs/design.md` `docs/task.md`を参照。
