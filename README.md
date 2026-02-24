# codex-logger

`codex-logger` は Codex CLI の `notify` で渡される JSON payload を受け取り、ローカルに保存する CLI です。  
`--telegram` を付けた場合のみ、`last-assistant-message` を Telegram topic へ送信します（任意機能）。

## Quickstart

```bash
# ローカル clone から実行（開発時）
uvx --from . codex-logger --help
```

`--help` は Telegram の環境変数が未設定でも実行できます。

## Run via uvx

`codex-logger` は `uvx` で実行します。通常運用は tag 固定を推奨し、緊急時のみ commit sha 固定を使います（詳細は ADR 参照）。

```bash
# GitHub（ref未固定。動作確認向け）
uvx --from git+https://github.com/chemitaro/codex-agent-logger codex-logger --help

# GitHub + tag 固定（推奨）
uvx --from git+https://github.com/chemitaro/codex-agent-logger@v0.1.0 codex-logger --help

# GitHub + commit sha 固定（緊急時）
uvx --from git+https://github.com/chemitaro/codex-agent-logger@<commit-sha> codex-logger --help

# ローカル clone から実行（開発時）
uvx --from /path/to/local/clone codex-logger --help
```

※ `@v0.1.0` は例です。実際に存在する tag に置き換えてください。

手動で payload を渡して検証する例です（実運用では `notify` が末尾に自動付与します）。

```bash
PAYLOAD='{"type":"agent-turn-complete","thread-id":"thread_123","turn-id":"turn_456","cwd":"'"$PWD"'","input-messages":["hello"],"last-assistant-message":"done"}'

uvx --from /path/to/local/clone codex-logger "$PAYLOAD"
uvx --from /path/to/local/clone codex-logger --telegram "$PAYLOAD"
```

## Codex `notify` integration

`notify` 設定では、Codex が JSON payload をコマンド引数の末尾に自動追加します。  
`codex-logger` 側で payload を手動追記する必要はありません。

Telegram なし:

```toml
# ~/.codex/config.toml
notify = ["uvx", "--from", "git+https://github.com/chemitaro/codex-agent-logger@v0.1.0", "codex-logger"]
```

Telegram あり:

```toml
# ~/.codex/config.toml
notify = ["uvx", "--from", "git+https://github.com/chemitaro/codex-agent-logger@v0.1.0", "codex-logger", "--telegram"]
```

※ `@v0.1.0` は例です。実際に存在する tag に置き換えてください。

## Telegram（任意）を使う場合の前提

- 対象チャットは **supergroup** を使用する
- supergroup で **topics（フォーラム）を有効化**する
- Bot を対象 supergroup に追加する
- Bot に topic 作成とメッセージ送信に必要な権限を付与する
- 機密値は README に直書きせず、環境変数または `.env` を使う

必要な環境変数:

```bash
TELEGRAM_BOT_TOKEN=<YOUR_TELEGRAM_BOT_TOKEN>
TELEGRAM_CHAT_ID=<YOUR_SUPERGROUP_CHAT_ID>
```

## env / .env 方針

`--telegram` 時の設定は次の方針です。

- `<cwd>/.env` を自動読込（存在する場合のみ）
- 優先順位は **実行時環境変数 > `<cwd>/.env`**
- `uvx --env-file` は任意（明示したい場合のみ）

`.env` 例（プレースホルダのみ）:

```dotenv
TELEGRAM_BOT_TOKEN=<YOUR_TELEGRAM_BOT_TOKEN>
TELEGRAM_CHAT_ID=<YOUR_SUPERGROUP_CHAT_ID>
```

`uvx --env-file` を明示する例（任意）:

```bash
uvx --env-file /path/to/.env --from git+https://github.com/chemitaro/codex-agent-logger@v0.1.0 codex-logger --telegram "$PAYLOAD"
```

## ログ出力先

ログは payload の `cwd`（なければ実行時 `cwd`）配下の `.codex-log/` に保存されます。

```text
<cwd>/.codex-log/
├── logs/
│   └── <ts>_<event-id>.json
├── summary.md
├── summary.lock
├── telegram-topics.json      # --telegram 利用時に作成
└── telegram-topics.lock      # --telegram 利用時に作成
```

補足:

- `logs/*.json` は 1イベント=1ファイル（raw payload）
- `summary.md` は `logs/*.json` から毎回再構築
- 誤コミット防止のため、`<cwd>/.gitignore` に `.codex-log/` を best-effort で自動追記します（無ければ作成 / 重複追記しない）
- `--telegram` はローカル保存成功後にベストエフォートで送信

## Troubleshooting

```bash
# CLI の確認
uvx --from . codex-logger --help
```

- `--telegram` で env 不足時は Telegram 送信をスキップし、警告を出します
- 機密値（Token / Chat ID）はコミットしないでください

## References

- `spec-dock/active/issue/requirement.md`
- `spec-dock/active/issue/design.md`
- `spec-dock/active/issue/plan.md`
- `spec-dock/active/initiative/adrs/adr-00001-notify-logger-output-and-telegram.md`
- `spec-dock/active/initiative/adrs/adr-00005-dotenv-loading-strategy.md`
- `spec-dock/active/initiative/adrs/adr-00006-uvx-ref-pinning-strategy.md`
- `spec-dock/active/initiative/artifacts/notify-payload.md`
- https://developers.openai.com/codex/config-advanced#notify
