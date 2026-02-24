---
種別: 設計書（Issue）
ID: "iss-00012"
タイトル: "Telegram delivery diagnostics"
関連GitHub: ["#12"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md"]
親: ["epic-00004", "init-00001"]
---

# iss-00012 Telegram delivery diagnostics — 設計（HOW）

## 目的・制約（要件から転記・圧縮） (必須)
- 目的: `--telegram` 指定時に送信がスキップ/失敗した理由を `.codex-log/telegram-errors/` に残す。
- MUST:
  - スキップ/失敗時に診断ログ（Markdown）を出す（best-effort）
  - 機密値は出さない
- MUST NOT:
  - Telegram に追加のエラー通知を送らない
  - `.codex-log/` 外へ出力しない
- 非交渉制約:
  - 依存追加なし
  - ローカル保存は必達（診断ログの失敗で exit non-zero にしない）

---

## 既存実装/規約の調査結果（As-Is / 99.9%理解） (必須)
- 参照した規約/実装（根拠）:
  - `AGENTS.md`: `.codex-log/` 配下に集約し、ローカル保存優先
  - `src/codex_logger/cli.py`: `--telegram` 指定時のみ Telegram を実行
  - `src/codex_logger/telegram.py`: 失敗/スキップ理由は stderr warn のみ
  - `src/codex_logger/atomic.py`: 原子的書き込みユーティリティ（tmp → replace）
- 観測した現状（事実）:
  - `notify` で stderr が見えない運用があり、配信失敗時に原因が追えない。
- 採用するパターン（命名/責務/例外/テスト）:
  - 「送信の結果（sent/skipped/failed）」を組み立て、失敗/スキップ時にのみ Markdown を生成する。
  - Markdown は `write_text_atomic` で原子的に置換（部分書き込みを残さない）。
  - 例外は握りつぶし（warning-only）、ローカル保存は継続。
- 影響範囲:
  - `src/codex_logger/telegram.py`（診断の生成）
  - `src/codex_logger/cli.py`（イベント識別子の受け渡し）
  - テスト追加/更新

## 主要フロー（AC単位） (任意)
- Flow for AC-001（env不足）:
  1) `--telegram` で呼ばれる
  2) env不足を検知して送信をスキップ
  3) `<cwd>/.codex-log/telegram-errors/<event>.md` を生成（best-effort）
- Flow for AC-002（API失敗）:
  1) topic 作成/送信で例外（TelegramError）
  2) `<event>.md` に失敗要約と確認ポイントを残す
- Flow for AC-003（成功）:
  1) 送信成功
  2) 診断ログは生成しない

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

participant "cli.main" as CLI
participant "telegram.send_last_message_best_effort" as TG
database ".codex-log/" as Dir
file "telegram-errors/<event>.md" as Err

CLI -> TG: send_last_message_best_effort(..., event_stem)
alt ok
  TG --> CLI: (return)
else skipped/failed
  TG -> Err: write markdown (atomic)\nno secrets
end
@enduml
```

## インターフェース契約（ここで固定） (任意)
- IF-001: `codex_logger.telegram.send_last_message_best_effort(raw_payload: str, *, base_cwd: Path, base_dir: Path, event_stem: str) -> None`
  - Input:
    - `raw_payload`: notify payload（JSON文字列）
    - `base_dir`: `<cwd>/.codex-log/`
    - `event_stem`: raw payload のログファイル stem（例: `<ts>_<event-id>`）。診断ログ命名の SSOT
  - Output: なし（best-effort）
  - Side-effects:
    - 成功: mapping 更新のみ
    - 失敗/スキップ: `base_dir/telegram-errors/<event>.md` の生成（best-effort）
  - Errors:
    - Telegram API/診断ログ出力の例外は握りつぶし、stderr warning のみ

## 診断ログ（Markdown）のフォーマット（最小） (必須)
- 出力先: `<cwd>/.codex-log/telegram-errors/<event>.md`
- 記載する項目:
  - outcome: `skipped` / `failed`
  - reason: env不足 / payload欠損 / invalid JSON / API error / network error ...
  - context（機密無し）:
    - `cwd`（payloadのcwd）
    - `thread-id` / `turn-id`（あれば）
    - chunk 情報（分割中の失敗なら `i/n`）
  - hint（次に確認すべきこと）: 例 `topics有効化`, `bot権限`, `chat_id`, `rate limit` 等
- 書かないこと:
  - token 値 / raw payload 全文 / input-messages 全文

## 変更計画（ファイルパス単位） (必須)
- 変更（Modify）:
  - `src/codex_logger/telegram.py`: スキップ/失敗時に診断ログを書き出す（event_stem を利用）
  - `src/codex_logger/cli.py`: `event_stem`（saved_path.stem）を telegram へ渡す
  - `README.md`: `telegram-errors/` を構成図へ追記（必要なら）
- 追加（Add）:
  - `tests/test_telegram_diagnostics.py`: env不足/HTTP失敗/成功時の診断ログ生成有無を検証
- 参照（Read only / context）:
  - `src/codex_logger/atomic.py`: 原子的書き込み
  - `tests/test_telegram_api_mock.py`: Telegram API モックの既存テスト

## マッピング（要件 → 設計） (必須)
- AC-001 → `telegram.send_last_message_best_effort`（env不足を診断ログへ）
- AC-002 → `telegram.send_last_message_best_effort`（TelegramError を診断ログへ）
- AC-003 → `telegram.send_last_message_best_effort`（成功時は診断ログ無し）
- AC-004 → `telegram.send_last_message_best_effort`（診断ログに機密/全文payloadが出ない）
- EC-001 → `telegram.send_last_message_best_effort`（invalid JSON / 欠損を診断ログへ）
- EC-002 → `telegram.send_last_message_best_effort`（診断ログ失敗は warning-only）
- EC-003 → `telegram.send_last_message_best_effort`（chunk index を可能な範囲で記録）

## テスト戦略（最低限ここまで具体化） (任意)
- 追加/更新するテスト:
  - Unit/Integration（APIモック）:
    - env不足 → 診断ログ生成、API未呼び出し
    - API失敗 → 診断ログ生成
    - 成功 → 診断ログが生成されない
    - 診断ログ本文に機密値（token 値）や raw payload 全文が含まれない
  - CLI 経由で event_stem が渡ること（最小の回帰テスト）
- 実行コマンド:
  - `uv run --frozen pytest -q`

## ディレクトリ/ファイル構成図（変更点の見取り図） (任意)
```text
<repo-root>/
├── src/codex_logger/
│   ├── cli.py                   # Modify
│   └── telegram.py               # Modify
└── tests/
    └── test_telegram_diagnostics.py  # Add
```

## 省略/例外メモ (必須)
- 該当なし
