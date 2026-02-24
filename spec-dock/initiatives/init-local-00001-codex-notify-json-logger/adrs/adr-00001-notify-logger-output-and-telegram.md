---
種別: ADR（Architecture Decision Record）
ID: "adr-00001"
タイトル: "Notify Logger Output and Telegram"
状態: "accepted"
作成者: "codex-agent"
最終更新: "2026-02-24"
親: ["init-local-00001"]
---

# adr-00001 Notify Logger Output and Telegram

## 結論（Decision） (必須)
- 結論:
  - Codex CLI の `notify` で受け取る JSON payload を、通知（OS側）には使わず **ローカルファイルへ保存**する。
  - ローカル保存は `<cwd>/.codex-log/` 配下に行い、`logs/` に「1イベント=1ファイル」を残し、`summary.md` は毎回フレッシュ生成する。
  - Telegram には token 情報等は送らず、`last-assistant-message`（最終アウトプット）だけを **セッション単位 topic**へ送信する。
- ログ保存先/構成:
  - ルート: `<cwd>/.codex-log/`
    - ここでの `<cwd>` は payload の `cwd` を正とし、正規化（realpath 相当）して採用する。
  - 個別ログ: `<cwd>/.codex-log/logs/<ts>_<thread-id>_<turn-id>.md`
  - 結合サマリ: `<cwd>/.codex-log/summary.md`
    - 更新方法: 受信のたびに `logs/` を時系列（ファイル名ソート）で結合して **フル再構築**する。
      - `summary.md` の再構築は同時実行で壊れないよう、再構築区間をロックする（例: `.codex-log/summary.lock` を用いた OS レベルの排他）。
      - 出力は `summary.md.tmp` に書き出してから原子的に置換する（失敗時は旧 `summary.md` を保持する）。
- ファイル命名:
  - `<ts>` は日時プレフィックス（例: `2026-02-24T09-53-12.345Z` のように、ソートしやすくファイル名として安全な形式）
  - 衝突回避として `thread-id` と `turn-id` を含める。
  - ただし `thread-id`/`turn-id` は **生でファイル名へ埋め込まない**（危険文字/長さ対策）。ファイル名は正規化（sanitize/短縮/ハッシュ等）した値を使い、生値は Markdown 本文と raw JSON に残す。
  - それでも同名が発生し得るため、ファイルは **排他的作成**（例: `O_EXCL` 相当）で書き込み、衝突時はサフィックス（例: `__01`, `__02`）を付けて必ず別名で保存する（上書きしない）。
- Markdown 保存フォーマット（方針）:
  - 先頭ヘッダーに `type`, `thread-id`, `turn-id`, `cwd` 等のメタ情報（＋存在すれば token 情報）を記録する。
  - 本文に `last-assistant-message` を人間が読みやすい形で記録する。
  - 末尾に raw JSON をコードブロックで保存する（完全性優先）。
  - 補足: 現行の `notify` payload には token 使用量は含まれないため、必要なら別経路（tokenizer 推定/OTel 等）で扱う。
  - セキュリティ（権限）: `.codex-log/` と `logs/` は 0700、ログファイルは 0600 を意図し、可能な範囲で restrictive に作成する（OS/FS が非対応の場合はベストエフォート）。
- Telegram 送信:
  - 前提: Telegram supergroup で topics（forum）を有効化し、Bot に topic 作成権限を付与する。
  - 送信先は環境変数で与える（例: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`）。
  - 送信するかどうかは CLI フラグで切り替える。
    - `--telegram` 指定時のみ Telegram 送信を行う（環境変数が揃っていても、フラグ無しなら送信しない）。
    - `--telegram` 指定があるのに環境変数が不足している場合は、送信せず **警告を stderr に出す**（ローカル保存は継続）。
  - topic は `thread-id`（=セッションID）単位で 1 つ作り、以後は再利用する。
    - そのために `<cwd>/.codex-log/telegram-topics.json` に `thread-id -> message_thread_id` の mapping を保存する。
    - mapping の更新は同時実行で破損しないよう、ロック + 一時ファイル経由の原子的置換で行う。
  - 文字数制限（4096 文字）超過時は **改行境界を優先**して分割し、複数投稿で全文を送る。
    - 改行が無い等で分割できない場合は、上限文字数で強制分割する（送信失敗を避ける）。
  - 失敗時ポリシー:
    - ローカル保存失敗: 非0終了（必達）
      - ローカル保存には「個別ログ」だけでなく「summary 再構築」も含む（個別ログ保存に成功していても summary 更新失敗は非0で検知可能にする）。
    - Telegram 送信失敗: stderr warn（ローカル保存優先、原則は 0 終了）
  - 未知イベント:
    - 未知の `type` でもローカル保存は行う（raw JSON は残す）。
    - Telegram 送信は行わない（未知イベントのため）。

## 背景（Context） (必須)
- 背景/制約（なぜ今決める必要があるか）:
  - Codex CLI の `notify` は、イベント発生時に任意コマンドを実行し、JSON payload を **コマンド引数として付与**する（追加引数がある場合は末尾になる）。
  - 今回は OS 通知を出すのではなく、この JSON payload を「1イベント=1ファイル」で保存し、必要に応じて Telegram へ最終アウトプットのみ配信したい。
- 前提:
  - `notify` の対象イベントは現時点で `agent-turn-complete` を想定する。
  - payload の共通フィールド例: `type`, `thread-id`, `turn-id`, `cwd`, `input-messages`, `last-assistant-message`。

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

actor "Codex CLI" as Codex
participant "codex-logger\n(handler)" as Handler
database ".codex-log/logs/*.md" as Logs
database ".codex-log/summary.md" as Summary
participant "Telegram\n(optional)" as TG

Codex -> Handler: exec notify cmd\n(+ payload json as arg)
Handler -> Logs: write 1-event=1-file\n(+ raw json)
Handler -> Summary: rebuild (atomic replace)
alt --telegram flag
  Handler -> TG: send last output\n(topic per thread-id)
else no flag
  Handler -> Handler: skip Telegram
end
@enduml
```

## 選択肢（Options considered） (必須)
- Option A: `<cwd>/.codex-log/` へ保存（採用）
  - 概要:
    - payload 内の `cwd` を基点に、隠しディレクトリ `.codex-log/` を作成してログを保存する。
    - 1イベント=1Markdown を `logs/` に保存し、`summary.md` は毎回フレッシュ生成する。
    - Telegram は supergroup の topics（forum）を前提に、`thread-id`（=セッション相当）ごとに topic を作成/再利用して送信する。
  - Pros:
    - 利用ディレクトリ直下を汚しにくい（開発中のノイズを抑制）
    - 収集対象（notify payload）を raw で保持しつつ、人間向けの Markdown も得られる
    - Telegram は「セッション単位」に整理できる
  - Cons:
    - topics を作るには bot 権限（`can_manage_topics` 等）や forum 有効化が必要
    - payload を raw で保存するため、機密/個人情報が含まれる場合の取り扱いが課題
- Option B: `<cwd>/codex-logs/` へ保存（非推奨）
  - 概要:
    - `codex-logs/` のような見えるディレクトリへログを保存する。
    - Telegram は topic を使わず単一スレッド/単一チャットへ送る。
  - Pros:
    - 目につきやすく運用が単純
  - Cons:
    - 作業ディレクトリ直下が散らかりやすい
    - topic を使わないとセッション単位で追いにくい
  - 棄却理由（棄却する場合）:
    - 「日時でソートしやすい 1メッセージ=1ファイル」の運用は Option A の方が相性が良い。

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true

folder "<cwd>/.codex-log" {
  folder "logs/" {
    file "<ts>_<thread>_<turn>.md"
  }
  file "summary.md"
  file "telegram-topics.json (optional)"
}
@enduml
```

## 判断理由（Rationale） (必須)
- 要件（1イベント=1ファイル、日時ソート、raw JSON 保持、Telegram は最終アウトプットのみ）との整合を優先する。
- ログは利用ディレクトリごとに閉じたい（`cwd` を基点にする）。

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true

note "SSOT=raw JSON\nTelegram=last output only" as N
N .. (Codex CLI)
@enduml
```

## 影響（Consequences） (必須)
- Positive（良い点）:
  - notify payload を失わずに保存でき、後から再解析/再送が可能になる
  - Telegram を「セッション別 topic」に整理できる
- Negative / Debt（悪い点 / 将来負債）:
  - Telegram 送信は外部流出リスクがある（送る内容の制御・マスキングの判断が必要）
  - Bot API の制約により「既存 topic の検索」が難しく、ローカルの mapping 保存が必要になる可能性が高い
- 影響範囲（コード/テスト/運用/データ）:
  - notify handler（CLI から呼ばれるスクリプト/バイナリ）
  - ログ保存ディレクトリとファイル形式（後方互換の考慮が必要）
- 移行/ロールバック:
  - 初期は新規導入のみ。失敗時は Telegram を無効化してファイル保存のみで継続可能にする。
- Follow-ups（追加の Epic/Issue/ADR）:
  - （必要なら）機密情報マスキング方針の ADR 分離

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true

rectangle "Local save (must)" as LS
rectangle "Telegram (optional)" as TG
LS --> TG : enabled by --telegram
@enduml
```

## 参考（References） (任意)
- 関連仕様（requirement/design/plan/report）:
  - `spec-dock/active/initiative/requirement.md`
  - `spec-dock/active/initiative/design.md`
  - `spec-dock/active/initiative/plan.md`
- PR/実装:
  - ...
- 外部資料:
  - https://developers.openai.com/codex/config-advanced#notify

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true

rectangle "Requirement/Design/Plan" as Specs
rectangle "Implementation" as Impl
rectangle "notify payload docs" as Docs

Specs --> Impl
Docs --> Impl
@enduml
```
