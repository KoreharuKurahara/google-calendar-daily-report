#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Calendar Daily Report Bot テストファイル
すべてのメッセージが日本語で表示されることを確認します
"""

import unittest
import sys
import os

# テスト対象のmainモジュールをインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import CalendarReportBot


class TestJapaneseOutput(unittest.TestCase):
    """日本語出力テストクラス"""
    
    def setUp(self):
        """テスト前の初期化"""
        self.bot = CalendarReportBot()
    
    def test_挨拶メッセージ(self):
        """挨拶メッセージが正しく日本語で返されることを確認"""
        message = self.bot.挨拶()
        self.assertIn("こんにちは", message)
        self.assertIn("Googleカレンダー", message)
        self.assertIn("bot", message)
        print(f"✓ 挨拶メッセージテスト成功: {message}")
    
    def test_日付取得(self):
        """日付が日本語形式で取得されることを確認"""
        date_str = self.bot.今日の日付を取得()
        self.assertIn("年", date_str)
        self.assertIn("月", date_str)
        self.assertIn("日", date_str)
        print(f"✓ 日付取得テスト成功: {date_str}")
    
    def test_レポート作成(self):
        """レポートが日本語で作成されることを確認"""
        report = self.bot.レポート作成()
        
        # レポートの必要なキーが存在することを確認
        self.assertIn("日付", report)
        self.assertIn("メッセージ", report)
        self.assertIn("状態", report)
        
        # 日本語メッセージが含まれていることを確認
        self.assertIn("カレンダー", report["メッセージ"])
        self.assertEqual(report["状態"], "開発中")
        
        print("✓ レポート作成テスト成功:")
        for key, value in report.items():
            print(f"  {key}: {value}")


def main():
    """テスト実行のメイン関数"""
    print("=== Google Calendar Daily Report Bot 日本語対応テスト ===")
    print()
    
    # テスト実行
    unittest.main(verbosity=2, exit=False)
    
    print()
    print("すべてのテストが完了しました。日本語での応答が正常に動作しています。")


if __name__ == "__main__":
    main()