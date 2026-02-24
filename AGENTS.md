# AGENTS.md（/srv/mount/codex-agent-logger）

## 言語
- ユーザーとの会話: 日本語
- 内部推論: 英語

## このリポジトリの目的（要点）
- ツール名/CLI: `codex-logger`
- 入力: Codex CLI `notify` が渡す JSON payload（**コマンド引数の末尾**）
- 出力（ローカル必達）: `<cwd>/.codex-log/`
  - `<cwd>/.codex-log/logs/` に 1イベント=1Markdown
  - `<cwd>/.codex-log/summary.md` は `logs/` から毎回フル再構築（`summary.md.tmp` → rename の原子置換）
- Telegram（任意）: `--telegram` 指定時のみ、`last-assistant-message` のみ送信（入力や raw JSON は送らない）

## 重要な仕様ソース（SSOT）
- Active pointers: `spec-dock/active/context-pack.md`
- Initiative: `spec-dock/active/initiative/{requirement,design,plan}.md`
- Epics:
  - `spec-dock/active/initiative/epics/epic-local-00003-packaging-and-cli/`
  - `spec-dock/active/initiative/epics/epic-local-00001-local-logging-and-summary/`
  - `spec-dock/active/initiative/epics/epic-local-00002-telegram-topics-delivery/`
- ADR: `spec-dock/active/initiative/adrs/adr-00001-notify-logger-output-and-telegram.md`
- 調査メモ: `spec-dock/active/initiative/artifacts/notify-payload.md`

## spec-dock コマンド（よく使う）
- Active 確認: `./spec-dock/scripts/spec-dock active show`
- Validate: `./spec-dock/scripts/spec-dock validate`
- Sync: `./spec-dock/scripts/spec-dock sync`

## 実行例（uvx）
```bash
# ローカル保存のみ
uvx --from git+https://github.com/<owner>/<repo> codex-logger '<payload-json>'

# Telegram 送信あり（最終アウトプットのみ）
uvx --from git+https://github.com/<owner>/<repo> codex-logger --telegram '<payload-json>'

# GitHub ref 固定（tag / commit）
uvx --from git+https://github.com/<owner>/<repo>@v0.1.0 codex-logger '<payload-json>'
uvx --from git+https://github.com/<owner>/<repo>@<commit-sha> codex-logger '<payload-json>'

# ローカルパス（clone 済み）
uvx --from /path/to/local/clone codex-logger '<payload-json>'
```

## Telegram 環境変数（予定）
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `.env` を使う場合は（原則）uvx 側の `--env-file` を使う（詳細は Epic 00003 の設計参照）

## マルチエージェント運用
- 実装前: reviewer エージェントで spec/ADR をレビュー
- 実装: dev_coder エージェントで TDD（Red/Green/Refactor）
- 実装後: reviewer で再レビュー

## Git 運用（安全）
- 破壊的操作（履歴改変/強制更新など）は禁止
- `git add` / `git commit` はユーザーの明示的な指示がある場合のみ
- コミットメッセージ: Conventional Commits（日本語、複数行必須）

