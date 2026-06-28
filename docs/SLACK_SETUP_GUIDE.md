# Slack アプリ設定ガイド (Slack App Setup Guide)

`kintai-sync` を動作させるために必要な Slack アプリの作成と設定手順を説明します。

---

## 1. Slack アプリの作成

1.  [Slack API: Applications](https://api.slack.com/apps) にアクセスします。
2.  **"Create New App"** をクリックします。
3.  **"From an app manifest"** を選択します。
4.  アプリをインストールするワークスペースを選択します。
5.  以下の Manifest (YAML) をコピーして貼り付けます。

### App Manifest (YAML)
`[YOUR_RECEIVER_URL]` は Cloud Run デプロイ後に取得できる Receiver の URL（例: `https://...a.run.app/slack/events`）に置き換えてください。

```yaml
display_information:
  name: kintai-sync
  description: 勤怠連絡の自動化（Jobcan/Calendar同期）
  background_color: "#2c2d30"
features:
  bot_user:
    display_name: Kintai Sync
    always_online: true
  event_subscriptions:
    request_url: [YOUR_RECEIVER_URL]
    bot_events:
      - message.channels
      - message.groups
oauth_config:
  scopes:
    user:
      - users.profile:write
    bot:
      - chat:write
      - users:read
      - users:read.email
      - channels:history
      - groups:history
settings:
  event_subscriptions:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

---

## 2. 権限 (Scopes) の確認

Manifest を使用した場合、以下の権限が自動的に設定されます。

- **Bot Token Scopes** (アプリとしての行動):
  - `chat:write`: 完了通知の返信、部署チャンネルへの報告。
  - `users:read`, `users:read.email`: ユーザー名とメールアドレス（カレンダー連携用）の取得。
  - `channels:history`: メッセージ内容の読み取り。
- **User Token Scopes** (ユーザー個人の操作):
  - `users.profile:write`: ユーザーの「ステータス（絵文字とテキスト）」の更新。

---

## 3. トークンの取得と保存

アプリをワークスペースにインストール後、以下の情報を取得し、Google Cloud の **Secret Manager** に保存します。

| 項目 | Slack API コンソールでの場所 | 保存先 Secret ID (推奨) |
| :--- | :--- | :--- |
| **Bot User OAuth Token** | OAuth & Permissions > `xoxb-...` | `kintai-sync-slack-bot-token` |
| **User OAuth Token** | OAuth & Permissions > `xoxp-...` | `SLACK_USER_TOKEN_[USER_ID]` |
| **Signing Secret** | Basic Information > `App Credentials` | `kintai-sync-slack-signing-secret` |

### User Token (xoxp-) について
ステータス更新機能（🌴 休暇中など）を利用する場合、各ユーザーにアプリを承認してもらい、個別の `xoxp-` トークンを取得する必要があります。

---

## 4. Secret Manager への登録コマンド

取得したトークンは、以下の `make` コマンドで登録できます。

```bash
# Botトークンの登録
make register-secrets

# ユーザーごとのトークン（ステータス更新用）の登録
# 例: gcloud secrets create SLACK_USER_TOKEN_U12345 --replication-policy="automatic"
#     echo -n "xoxp-..." | gcloud secrets versions add SLACK_USER_TOKEN_U12345 --data-file=-
```

---

## 5. 最後の仕上げ

Slack アプリの設定画面（Event Subscriptions）で **Request URL** が `Verified` になっていることを確認してください。

1. `make deploy` で Cloud Run をデプロイ。
2. 表示された URL を Slack API コンソールの `Request URL` に入力。
3. `Verified` と表示されれば接続成功です。
