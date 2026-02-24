---
種別: 要件定義書（Issue）
ID: "iss-00012"
タイトル: "Telegram delivery diagnostics"
関連GitHub: ["#12"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
親: ["epic-00004", "init-00001"]
---

# iss-00012 Telegram delivery diagnostics — 要件定義（WHAT / WHY）

## 目的（ユーザーに見える成果 / To-Be） (必須)
- `codex-logger --telegram` が「送れていない」場合でも、理由が **`<cwd>/.codex-log/` 配下の診断ログ**から分かる。
- Codex CLI `notify` 経由で stderr が見えない環境でも、Telegram 配信失敗をデバッグできる（ローカル保存は必達）。

## 背景・現状（As-Is / 調査メモ） (必須)
- 現状の挙動（事実）:
  - `--telegram` 時の失敗/スキップ理由は、主に stderr の `warn:` に出る（ファイルには残らない）。
- 現状の課題（困っていること）:
  - Codex CLI `notify` 経由では stderr が観測できないことがあり、Telegram が届かない時に原因が追えない。
- 再現手順（最小で）:
  1) `notify` に `codex-logger --telegram` を設定する
  2) Telegram に投稿されない（または topic 作成できない）が、ユーザー側でエラーが見えない
- 観測点（どこを見て確認するか）:
  - filesystem: `<cwd>/.codex-log/telegram-errors/*.md`
  - filesystem: `<cwd>/.codex-log/telegram-topics.json`（topic mapping）
  - filesystem: `<cwd>/.codex-log/logs/*.json`（raw payload）
- 情報源（ヒアリング/調査の根拠）:
  - Issue/チケット: #12
  - 既存実装: `src/codex_logger/telegram.py`（stderr warn のみ）
  - 既存実装: `src/codex_logger/cli.py`（`--telegram` が有効化条件）

## 対象ユーザー / 利用シナリオ (任意)
- 主な利用者（ロール）:
  - Codex CLI `notify` に `codex-logger --telegram` を設定して運用する開発者
- 代表的なシナリオ:
  - Telegram が届かない時に、`.codex-log/telegram-errors/` を見て原因を特定する（env不足/権限不足/ネットワーク等）

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

actor "Codex CLI" as Codex
participant "codex-logger" as Logger
participant "telegram.send_last_message_best_effort" as TG
database ".codex-log/" as Dir
file "telegram-errors/<event>.md" as Err

Codex -> Logger: notify(payload json)
Logger -> TG: --telegram?
alt delivered
  TG --> Logger: ok
else skipped/failed
  TG -> Err: write diagnostics (best-effort)\n(no secrets)
end
@enduml
```

## ディレクトリ/ファイル構成（出力の見取り図） (必須)
```text
<cwd>/.codex-log/
├── logs/
│   └── <ts>_<event-id>.json
├── summary.md
├── telegram-topics.json
├── telegram-topics.lock
└── telegram-errors/
    └── <ts>_<event-id>.md
```

## スコープ（暴走防止のガードレール） (必須)
- MUST（必ずやる）:
  - `--telegram` 指定時、送信が **スキップ/失敗**した場合は診断ログを `<cwd>/.codex-log/telegram-errors/` に保存する。
  - 診断ログは 1イベント=1ファイル（raw payload のログファイルと紐づく名前）とし、日時順に並ぶ。
  - 診断ログには「失敗/スキップ理由」「例外メッセージ（あれば）」「推奨確認ポイント」を含める。
  - 診断ログ出力に失敗しても、ローカル保存は継続する（warning のみ）。
- MUST NOT（絶対にやらない／追加しない）:
  - `TELEGRAM_BOT_TOKEN` など機密値を診断ログに出力しない（存在有無は可）。
  - `input-messages` や raw JSON を診断ログへ丸ごと転記しない。
  - Telegram に追加メッセージ（エラー通知）を送らない（このIssueでは行わない）。
- OUT OF SCOPE:
  - Telegram 以外の通知チャネル
  - 成功時の配信監査ログ（送信成功ログの永続化）

## 境界（Always / Ask / Never） (必須)
- Always（常に守る）:
  - Telegram 配信はベストエフォート（ローカル保存優先）。
  - 診断ログは `.codex-log/` 配下のみ（外部を汚染しない）。
- Ask（迷ったら相談）:
  - 診断ログを「成功時にも出すか」の方針変更
- Never（絶対にしない）:
  - 機密値（token 等）をファイル/標準出力へ出す

## 非交渉制約（守るべき制約） (必須)
- 依存追加はしない（標準ライブラリ + 既存ユーティリティで実装する）。
- CLI 契約（`codex-logger [--telegram] <payload-json>`）を壊さない。
- 診断ログは機密値を含めない。

## 前提（Assumptions） (必須)
- `<cwd>/.codex-log/` は作成/書き込み可能である（ローカル保存が前提）。
- Telegram の supergroup / topics 設定や Bot 権限は利用者側で行う。

## 判断材料/トレードオフ（Decision / Trade-offs） (任意)
- 論点: 診断ログの形（1イベント=1ファイル vs 単一ファイル追記）
  - 選択肢A: 1イベント=1ファイル（Pros: raw と紐づく/ロック不要/並列に強い / Cons: ファイル数が増える）
  - 選択肢B: 単一ファイル追記（Pros: 1箇所で見れる / Cons: 同時実行で壊れやすい）
  - 決定: **1イベント=1ファイル**
  - 理由: raw ログ（1イベント=1json）と整合し、事故が少ない。

## リスク/懸念（Risks） (任意)
- R-001: 診断ログが冗長になり機密を含む（影響: 漏洩 / 対応: 出力キーを最小化し、値はマスク/存在有無のみ）
- R-002: 診断ログ出力自体が失敗（影響: 追えない / 対応: stderr warn を維持し、ローカル保存は継続）

## 受け入れ条件（観測可能な振る舞い） (必須)
- AC-001:
  - Actor/Role: 開発者
  - Given: `--telegram` を付けて実行し、`TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` が不足している
  - When: `codex-logger` を実行する
  - Then: Telegram API は呼ばれず、`<cwd>/.codex-log/telegram-errors/<event>.md` に理由が保存される
  - 観測点: filesystem（診断ログ）/ HTTP（テストでは `urlopen` が呼ばれないこと）
- AC-002:
  - Actor/Role: 開発者
  - Given: `--telegram` を付けて実行し、Telegram API が失敗する（HTTP 4xx/5xx, ok=false, network error）
  - When: `codex-logger` を実行する
  - Then: ローカル保存は成功し、`<cwd>/.codex-log/telegram-errors/<event>.md` に失敗内容が保存される
  - 観測点: filesystem（診断ログ）
- AC-003:
  - Actor/Role: 開発者
  - Given: `--telegram` を付けて実行し、Telegram 送信が成功する
  - When: `codex-logger` を実行する
  - Then: `telegram-errors/` に当該イベントの診断ログが作られない
  - 観測点: filesystem
- AC-004:
  - Actor/Role: 開発者
  - Given: 診断ログが生成される（スキップ/失敗の任意ケース）
  - When: `<cwd>/.codex-log/telegram-errors/<event>.md` を読む
  - Then: 診断ログ本文に `TELEGRAM_BOT_TOKEN` の値や raw payload 全文が含まれない
  - 観測点: filesystem（診断ログ本文）

### 入力→出力例 (任意)
- EX-001:
  - Input: `codex-logger --telegram '<payload-json>'`（env 不足）
  - Output: `.codex-log/telegram-errors/<ts>_<event-id>.md` に「env不足」の記録

## 例外・エッジケース（仕様として固定） (必須)
- EC-001:
  - 条件: payload が不正 JSON、または `thread-id` / `last-assistant-message` が欠損している
  - 期待: Telegram は送られず、診断ログにスキップ理由が保存される
  - 観測点: filesystem（診断ログ）
- EC-002:
  - 条件: 診断ログの書き込みに失敗（read-only 等）
  - 期待: stderr に warning を出して継続し、ローカル保存は成功する
  - 観測点: stderr / exit code
- EC-003:
  - 条件: 送信が複数chunkに分割され、途中で失敗する
  - 期待: 診断ログに「何番目のchunkで失敗したか」が残る（可能な範囲で）
  - 観測点: filesystem（診断ログ）

## 用語（ドメイン語彙） (必須)
- TERM-001: 診断ログ = Telegram 送信がスキップ/失敗した理由を残す Markdown ファイル
- TERM-002: `<event>` = raw payload のログファイル名 stem（例: `<ts>_<event-id>`）

## 未確定事項（TBD / 要確認） (必須)
- 該当なし

## Definition of Ready（着手可能条件） (必須)
- [ ] 目的が 1〜3行で明確になっている
- [ ] MUST/MUST NOT/OUT OF SCOPE が書けている
- [ ] Always/Ask/Never が書けている
- [ ] AC/EC が観測可能（テスト可能）な形になっている
- [ ] 観測点（filesystem/stderr）が明記されている
- [ ] 未確定事項が整理されている（該当なしでもよい）

## 完了条件（Definition of Done） (必須)
- すべてのAC/ECが満たされる
- MUST NOT / OUT OF SCOPE を破っていない

## 省略/例外メモ (必須)
- 該当なし
