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
- [x] Terraform ベース構成の作成 (`terraform/*.tf`)
  - [x] プロジェクト初期設定 (API有効化)
  - [ ] 状態管理用バケットの作成 (`kintai-sync-tfstate-*`)
  - [x] Firestore データベースの定義
- [x] 共通サービスアカウントの定義 (`kintai-sync-*-sa`)

## フェーズ 2: 共通モジュール・設定管理の実装
- [x] Firestore 連携・履歴管理の実装 (`src/history.py`)
- [x] Secret Manager 連携モジュールの実装 (`src/secrets.py`)
- [x] Googleスプレッドシート同期ロジックの実装 (`src/sync.py`)
- [x] 各種外部連携モジュールの実装 (`slack.py`, `calendar.py`, `jobcan.py`)
- [ ] ログ・スクリーンショット保存機能の完成 (GCS連携の詳細)
- [ ] [手動タスク] Secret Manager への初期シークレット登録

## フェーズ 3: コアロジック（メッセージ解析と外部連携）の実装
- [x] Vertex AI (Gemini API) によるメッセージ解析ロジック (`src/parser.py`)
- [x] Worker サービスのメインロジック実装 (`src/main.py`)
- [x] Receiver サービスのメインロジック実装 (`src/receiver.py`)
## フェーズ 4: サーバーレスアーキテクチャの構築
- [x] 各サービスの Dockerfile 作成 (`Dockerfile.*`)
- [x] Cloud Tasks キューの定義 (Terraform)
- [x] 各サービスの Cloud Run デプロイ設定 (Terraform)
- [x] IAM 権限 (Roles) の詳細設定 (Terraform)
- [x] 定期実行設定 (Cloud Scheduler / 同期ロジック用)

## フェーズ 5: テスト・品質保証
- [x] 各モジュールのユニットテスト作成 (`tests/`)
- [ ] 疎通テスト（Slack -> Cloud Run -> Cloud Tasks -> Worker）
- [x] 冪等性（二重実行防止）の検証 (Firestore設計による)


## フェーズ 6: デプロイ・運用準備
- [ ] 本番環境への全リソースデプロイ
- [ ] マスター設定用スプレッドシートの作成・共有

---
*最終更新日: 2026年6月27日*
