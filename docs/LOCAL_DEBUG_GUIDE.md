# ローカルデバッグガイド

このドキュメントでは、`kintai-sync` の開発においてローカル環境で動作確認やデバッグを行う手順について説明します。

## 1. 準備

ローカル環境でスクリプトを実行するために、以下のセットアップが必要です。

### 依存関係のインストール
`uv` を使用して、必要なライブラリとブラウザ（Playwright）をインストールします。

```bash
# Python 依存関係の同期
uv sync

# Playwright ブラウザのインストール（ジョブカンの自動操作に必要）
uv run playwright install chromium
```

## 2. ジョブカン連携の動作確認

ジョブカンの自動ログインと申請ロジックを、実際のブラウザを使用してローカルでテストできます。

### 基本的な実行
以下のコマンドを実行すると、対話形式で認証情報とテスト内容を入力できます。

```bash
make verify-jobcan
```

### デバッグ機能

#### ブラウザ画面を表示する
デフォルトではブラウザはバックグラウンド（Headlessモード）で動きますが、実際の動きを目視で確認したい場合は、環境変数を指定します。

```bash
JOBCAN_HEADLESS=false make verify-jobcan
```

#### スクリーンショットの確認
操作に失敗した場合、自動的にエラー時点のスクリーンショットがプロジェクトルートに保存されます。
- ファイル名形式: `error_YYYY-MM-DD_スタッフコード.png`

## 3. 自然言語解析（Parser）のテスト

メッセージから勤怠情報を抽出するロジックは Vertex AI (Gemini) を使用しています。

### ユニットテストの実行
モックを使用した解析ロジックのテストは以下で実行できます。

```bash
# 全テストの実行
make test

# Parser に絞って実行
uv run pytest tests/test_parser.py
```

### (参考) 実際の API を使った確認
現在は直接的な検証スクリプトはありませんが、`src/parser.py` を直接読み込んで実行することで確認可能です。
※ Google Cloud の認証 (`gcloud auth application-default login`) が必要です。

## 4. ログの確認（Cloud Run）

デプロイ後の動作に問題がある場合は、ローカルから最新の実行ログをストリーミングで確認できます。

```bash
make logs
```

## 5. よくあるトラブルシューティング

- **Playwright が動かない**: `uv run playwright install chromium` を実行したか確認してください。
- **ログインに失敗する**: 企業ID、スタッフコード、パスワードが正しいか、`make verify-jobcan` の対話入力で確認してください。
- **Vertex AI の権限エラー**: `gcloud auth application-default login` を実行して、ローカル環境に認証情報を通してください。
