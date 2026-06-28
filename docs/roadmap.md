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
- [x] **[自動化]** ライフサイクル管理コマンドの構築 (`Makefile`)
  - [x] ブートストラップ自動化 (`make setup`)
  - [x] イメージビルド・PUSH自動化 (`make build`, `make push`)
  - [x] 秘密情報・ユーザー登録の自動化 (`make register-secrets`, `make register-user`)
  - [x] インフラ破棄の分離 (`make destroy` / `make destroy-all`)

## フェーズ 2: 共通モジュール・設定管理の実装

- [x] 外部連携モジュールの設定値外部化
- [x] Firestore 連携・履歴管理の実装 (`src/history.py`)
- [x] Secret Manager 連携モジュールの実装 (`src/secrets.py`)
- [x] Googleスプレッドシート同期ロジックの実装 (`src/sync.py`、Worker からの遅延読み込みキャッシュとして利用)
- [x] 各種外部連携モジュールの実装 (`slack.py`, `calendar.py`, `jobcan.py`)

## フェーズ 3: コアロジック（メッセージ解析と外部連携）の実装

- [x] Vertex AI (Gemini 3 Flash Preview) によるメッセージ解析ロジック (`src/parser.py`)
- [x] Worker サービスのメインロジック実装 (`src/main.py`)
- [x] Receiver サービスのメインロジック実装 (`src/receiver.py`)

## フェーズ 4: サーバーレスアーキテクチャの構築

- [x] 各サービスの Dockerfile 作成 (`Dockerfile.*`)
- [x] Cloud Run デプロイ設定 (Terraform)
- [x] 設定同期方式の決定（GAS / Cloud Scheduler を廃止し、Worker による遅延読み込みキャッシュへ移行）

## フェーズ 5: テスト・品質保証

- [x] 各モジュールのユニットテスト作成 (`tests/`)
- [x] 結合テスト・カバレッジ検証 (85%+ 達成)
- [x] 冪等性（二重実行防止）の検証 (Firestore設計)
- [x] **[追加]** サブタスクごとの実行状態管理と自動リトライ基盤の構築

## フェーズ 6: デプロイ・運用準備 (最終仕上げ)

- [x] **[基盤]** 設定用テンプレート生成コマンドの作成 (`make template`)
- [x] **[自動化]** 開発・運用ツールの拡充
  - [x] プリフライトチェック機能 (`make check`)
  - [x] コード品質管理の導入 (`make lint` / ruff)
  - [x] アーティファクトクリーンアップ (`make prune`)
- [x] **[自動化]** デプロイパイプラインの統合 (`make deploy`)
- [x] **[AI] AI 解析の精度向上と最適化フローの構築**
  - [x] 否定形（「休みません」）に対応するスマートフィルタリングロジックの実装
  - [x] プロンプト最適化用データの自動生成・アップロード (`make prepare-test`)
  - [x] Few-Shot Prompt Optimization プロセスのドキュメント化
- [x] **[機能] Worker ロジックの完全実装**
  - [x] Google カレンダー連携の有効化
  - [x] Slack ステータス（絵文字・テキスト）自動更新の実装
  - [x] 部署チャンネルへの自動報告フローの完成
- [ ] **[実行]** 実際のデプロイ作業の実施 (`make setup` -> `make deploy`)
- [ ] **[実行]** Secret Manager への実トークン/パスワード登録
  - [ ] `kintai-sync-slack-bot-token`
  - [ ] `kintai-sync-slack-signing-secret`
  - [ ] `JOBCAN_PASSWORD_[staff_code]` (各ユーザー分)
  - [ ] `SLACK_USER_TOKEN_[user_id]` (ステータス更新用、各ユーザー分)
- [ ] **[権限]** 設定スプレッドシート読み取り用 OAuth トークンの登録
  - [ ] GCP コンソールで OAuth 2.0 クライアントID (Desktop app) を作成し client_secret を取得
  - [ ] OAuth 同意画面を Internal に設定（リフレッシュトークンの失効回避）
  - [ ] `make register-sheets-oauth` でトークンを Secret Manager に登録
- [ ] **[権限]** Google Calendar API のドメイン全体の委任、または OAuth 認証の完了
- [x] **[検証]** ユニットテストによるロジック検証 (`make test`)
- [ ] **[検証]** 実際の Slack 投稿によるエンドツーエンドの疎通テスト

## フェーズ 7: プロダクション・ハードニング (安全性と運用の強化)

- [ ] **[セキュリティ]** Slack Webhook 署名検証の有効化 (`receiver.py`)
- [ ] **[セキュリティ]** 内部 API (Worker) の OIDC 認証による保護
- [ ] **[解析向上]** 複数日の同時申請への対応 (日付リスト抽出のサポート)
- [ ] **[運用監視]** Cloud Logging による異常検知とアラート通知の構築
- [ ] **[インフラ]** Cloud Tasks のリトライポリシーの最適化 (Terraform)

______________________________________________________________________

*最終更新日: 2026年6月28日*
