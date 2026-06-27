# kintai-sync 開発ロードマップ

このドキュメントは、`kintai-sync` システムの構築に向けたタスクを整理し、進捗を管理するためのものです。

## フェーズ 0: データ定義とバリデーション (堅牢性の基礎)

- [x] Pydantic によるデータモデルの定義 (`src/models.py`)

## フェーズ 1: プロジェクト初期化と基盤構築

- [x] 要件定義の策定 (v2.3.0)
- [x] パッケージマネージャーの移行 (`requirements.txt` -> `uv`)
- [x] 依存ライブラリの定義 (`pyproject.toml`)
- [x] システム設定の一元管理化 (`config.yaml`, `src/config.py`)
- [x] Terraform ベース構成の作成 (`terraform/*.tf`)
  - [x] API有効化 / SA定義 / Firestore / Cloud Tasks
  - [x] Artifact Registry / Secret Manager 定義
  - [x] 削除ポリシーの徹底 (`force_destroy`, `deletion_policy`)
- [x] **[基盤]** ライフサイクル自動化コマンドの構築 (`Makefile`)
  - [x] ブートストラップ自動化 (`make setup`)
  - [x] ログ確認・管理コマンド (`make logs`, `make secrets`)
  - [x] ユーザー追加自動化 (`make register-user`)
  - [x] インフラ破棄の分離 (`make destroy` / `make destroy-all`)

## フェーズ 2: 共通モジュール・設定管理の実装

- [x] 外部連携モジュールの設定値外部化
- [x] Firestore 連携・履歴管理の実装 (`src/history.py`)
- [x] Secret Manager 連携モジュールの実装 (`src/secrets.py`)
- [x] Googleスプレッドシート同期ロジックの実装 (`src/sync.py`)
- [x] 各種外部連携モジュールの実装 (`slack.py`, `calendar.py`, `jobcan.py`)

## フェーズ 3: コアロジック（メッセージ解析と外部連携）の実装

- [x] Vertex AI (Gemini API) によるメッセージ解析ロジック (`src/parser.py`)
- [x] Worker サービスのメインロジック実装 (`src/main.py`)
- [x] Receiver サービスのメインロジック実装 (`src/receiver.py`)

## フェーズ 4: サーバーレスアーキテクチャの構築

- [x] 各サービスの Dockerfile 作成 (`Dockerfile.*`)
- [x] Cloud Run デプロイ設定 (Terraform)
- [x] イベントベース同期の設定 (GAS 連携用 Webhook)

## フェーズ 5: テスト・品質保証

- [x] 各モジュールのユニットテスト作成 (`tests/`)
- [x] 結合テスト・カバレッジ検証 (90% 達成)
- [x] 冪等性（二重実行防止）の検証 (Firestore設計)

## フェーズ 6: デプロイ・運用準備 (最終仕上げ)

- [x] **[基盤]** 設定用テンプレート生成コマンドの作成 (`make template`)
- [x] **[基盤]** 開発・運用ツールの拡充
  - [x] プリフライトチェック機能 (`make check`)
  - [x] コード品質管理の導入 (`make lint` / ruff)
  - [x] アーティファクトクリーンアップ (`make prune`)
- [ ] **[準備]** Artifact Registry への Docker イメージ PUSH (`docker build & push`)
- [x] **[展開]** Terraform による本番環境デプロイ自動化 (`make deploy`)
- [ ] **[設定]** Secret Manager への実トークン/パスワード登録
  - [ ] `kintai-sync-slack-bot-token`
  - [ ] `kintai-sync-slack-signing-secret`
  - [ ] `JOBCAN_PASSWORD_[staff_code]` (各ユーザー分)
- [ ] **[連携]** スプレッドシートへの Google Apps Script の設定 (`google_apps_script.js`)
- [ ] **[権限]** Google Calendar API のドメイン全体の委任、または OAuth 認証の完了
- [x] **[検証]** ユニットテストによるロジック検証 (`make test`)
- [ ] **[検証]** 実際の Slack 投稿によるエンドツーエンドの疎通テスト

______________________________________________________________________

*最終更新日: 2026年6月27日*
