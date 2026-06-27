# kintai-sync 開発ロードマップ

このドキュメントは、`kintai-sync` システムの構築に向けたタスクを整理し、進捗を管理するためのものです。

## フェーズ 0: データ定義とバリデーション (堅牢性の基礎)
- [x] Pydantic によるデータモデルの定義 (`src/models.py`)
  - [x] ユーザー設定モデル (`UserSettings`)
  - [x] 勤怠情報モデル (`AttendanceInfo`)
  - [x] 実行ステータスモデル (`TaskExecutionState`)

## フェーズ 1: プロジェクト初期化と基盤構築
- [x] 要件定義の策定 (v2.2.0)
- [x] 依存ライブラリの定義 (`requirements.txt`)
- [ ] Terraform ベース構成の作成
  - [ ] プロジェクト初期設定 (API有効化)
  - [ ] 状態管理用バケットの作成 (`kintai-sync-tfstate-*`)
- [ ] 共通サービスアカウントの作成

## フェーズ 2: 共通モジュール・設定管理の実装
- [x] Firestore 連携・履歴管理の実装 (`src/history.py`)
- [ ] Secret Manager 連携モジュールの実装 (`src/secrets.py`)
- [ ] **Googleスプレッドシート同期ロジックの実装 (`src/sync.py`)** <-- 次の優先タスク
- [ ] ログ・スクリーンショット保存機能の実装 (GCS連携)

## フェーズ 3: コアロジック（メッセージ解析と外部連携）の実装
- [ ] Vertex AI (Gemini API) によるメッセージ解析ロジック
- [ ] Playwright によるジョブカン自動申請の実装 (`src/jobcan.py`)
- [ ] Slack Web API 連携（通知・ステータス変更）の実装 (`src/slack.py`)
- [ ] Google Calendar API 連携の実装 (`src/calendar.py`)

## フェーズ 4: サーバーレスアーキテクチャの構築
- [ ] Receiver サービス (Webhook 受信・Tasks エンキュー) の実装
- [ ] Cloud Tasks キューの構築
- [ ] Worker サービス (非同期実行エンジン) の実装
- [ ] 各サービスの Cloud Run デプロイ設定 (Terraform)

## フェーズ 5: テスト・品質保証
- [ ] 各モジュールのユニットテスト作成 (`tests/`)
- [ ] 疎通テスト（Slack -> Cloud Run -> Cloud Tasks -> Worker）
- [ ] エラーハンドリング・リトライ挙動の確認
- [ ] べき等性の検証

## フェーズ 6: デプロイ・運用準備
- [ ] 本番環境への全リソースデプロイ
- [ ] マスター設定用スプレッドシートの作成・共有
- [ ] 利用者向けマニュアル/簡易ガイドの作成
- [ ] 運用監視（Cloud Logging / Dashboard）の設定

---
*最終更新日: 2026年6月27日*
