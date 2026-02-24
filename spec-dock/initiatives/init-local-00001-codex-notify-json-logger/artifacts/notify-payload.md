---
種別: 調査メモ
タイトル: "Codex CLI notify payload（現行仕様）"
最終更新: "2026-02-24"
---

# Codex CLI notify payload（現行仕様）

## 目的
- `notify` handler 実装の前提（入力の JSON 構造/渡され方/イベント種別）を固定する。

## 結論（要点）
- `notify` は **単一のコマンド引数**として JSON 文字列を渡す（stdin ではない）。
- 現時点で `notify` が出すイベントは **`agent-turn-complete` のみ**。
- common fields（現行の主要キー）は次の 6 つ:
  - `type`
  - `thread-id`
  - `turn-id`
  - `cwd`
  - `input-messages`
  - `last-assistant-message`
- token 使用量は `notify` payload には含まれない（必要なら別経路で扱う）。

## 互換性ルール（このプロジェクト側の取り扱い方針）
- 必須フィールド（MVP）:
  - `type`, `thread-id`, `turn-id`, `cwd`
- 任意フィールド:
  - `input-messages`, `last-assistant-message`
- 未知フィールド:
  - 受信側は **無視してよい**（ただし raw JSON は保存する）
- 欠損フィールド:
  - 任意フィールドの欠損は許容する
  - 必須フィールド欠損はローカル保存は可能な限り行い、stderr に warn を出す（処理継続方針は実装で確定）
- 未知 `type`:
  - ローカル保存は行い、Telegram 送信は行わない（未知イベントのため）

## 再構成サンプル
```json
{
  "type": "agent-turn-complete",
  "thread-id": "<thread>",
  "turn-id": "<turn>",
  "cwd": "<working-directory>",
  "input-messages": ["<user prompt 1>", "<user prompt 2>"],
  "last-assistant-message": "<assistant final message>"
}
```

## 参考
- Codex docs: `notify`（official）
  - https://developers.openai.com/codex/config-advanced#notify
- openai/codex source（notify payload の実装）
  - https://raw.githubusercontent.com/openai/codex/main/codex-rs/core/src/user_notification.rs
