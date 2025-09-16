#!/bin/zsh
# Lambdaデプロイ自動化スクリプト
# 必要: AWS CLI, zip, Lambda関数名, IAM権限

set -e

LAMBDA_FUNCTION_NAME="kurahara-google-calendar-daily-reporter"  # ←適宜修正

ZIP_FILE="lambda_function.zip"

# 既存zipのみ削除（認証情報ファイルは削除しない）
rm -f $ZIP_FILE

# 1. 依存パッケージをvendorディレクトリにインストール
rm -rf vendor
mkdir vendor
pip install --target ./vendor -r requirements.txt

# 2. 必要ファイルをzip化（credentials.json, serviceaccount-credentials.jsonは絶対に含めない）
cd vendor
zip -r9 ../$ZIP_FILE .
cd ..
zip -g $ZIP_FILE lambda_function.py color-settings.json
# zip内容確認用（デバッグ用）
# unzip -l $ZIP_FILE

# 3. Lambdaへデプロイ
AWS_PROFILE=$(grep '^AWS_PROFILE=' .env | cut -d '=' -f2 | tr -d '\r\n')
AWS_REGION=$(grep '^AWS_REGION=' .env | cut -d '=' -f2 | tr -d '\r\n')
aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --zip-file fileb://$ZIP_FILE --profile $AWS_PROFILE --region $AWS_REGION

echo "デプロイ完了: $LAMBDA_FUNCTION_NAME"
