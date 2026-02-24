---
種別: 要件定義書（Issue）
ID: "iss-00010"
タイトル: "Telegram Topic Mapping and Send"
関連GitHub: ["#10"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
親: ["epic-00004", "init-00001"]
---

# iss-00010 Telegram Topic Mapping and Send — 要件定義（WHAT / WHY）

## 目的（ユーザーに見える成果 / To-Be） (必須)
- `--telegram` 指定時のみ、`last-assistant-message`（最終アウトプット）を Telegram topic に送信できる。
- topic はセッション（`thread-id`）単位で作成/再利用し、mapping を永続化できる。

## 背景・現状（As-Is / 調査メモ） (必須)
- 現状の挙動（事実）:
  - Telegram 送信は未実装。
- 現状の課題（困っていること）:
  - 最終アウトプットをセッション単位の topic に集約して受け取りたい。
  - 4096 文字制限を超える長文を、行の途中で切らず読みやすく分割したい。
- 観測点（どこを見て確認するか）:
  - Telegram: topic 作成/再利用、投稿
  - FS: `.codex-log/telegram-topics.json`
- 情報源（ヒアリング/調査の根拠）:
  - ADR: `adr-00002`（topic名）, `adr-00007`（分割連番）, `adr-00008`（exit code）, `adr-00005`（.env）

## 対象ユーザー / 利用シナリオ (任意)
- 主な利用者（ロール）:
  - ...
- 代表的なシナリオ:
  - ...

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

actor "Codex CLI" as Codex
participant "codex-logger" as Handler
database ".codex-log/telegram-topics.json" as Map
cloud "Telegram Bot API" as TG

Codex -> Handler: exec notify\n(+ payload json)
alt --telegram flag
  Handler -> Map: load mapping
  Handler -> TG: createForumTopic (if missing)
  Handler -> Map: save mapping\n(lock + atomic replace)
  Handler -> TG: sendMessage (chunked)\n(message_thread_id)
else no flag
  Handler -> Handler: skip Telegram
end
@enduml
```

## スコープ（暴走防止のガードレール） (必須)
- MUST（必ずやる）:
  - `--telegram` 指定時のみ Telegram を送信する（未指定なら送らない）。
  - Telegram 送信の必須 payload 項目を固定する:
    - 必須: `thread-id`（非空文字列）, `last-assistant-message`（非空文字列）
    - 任意: `cwd`（欠損時は実行時 cwd の basename を topic 名に使う）
    - 必須項目が満たせない場合は warn + **送信フロー全体を skip**（topic 作成・mapping 更新・投稿を行わない）
  - `thread-id` 単位で topic を作成/再利用し、mapping を `.codex-log/telegram-topics.json` に保存する。
    - `telegram-topics.json` の read-modify-write は **ロックで排他**し、`tmp -> atomic replace` で破損を防ぐ（並行実行対策）。
  - topic 名は `<cwd_basename> (<thread-id>)`（長さ短縮は `adr-00002`）。
  - 4096 超過時は改行優先で分割し、各 chunk に `(i/n)\\n` を付与する（`adr-00007`）。
  - `.env` は `<cwd>/.env` を自動読込（存在する場合のみ、環境変数優先: `adr-00005`）。
    - ここでの `<cwd>` は payload の `cwd` を正とし、欠損時は実行時 cwd を用いる
  - Telegram 失敗は warn + exit 0（ローカル保存成功時。`adr-00008`）。
- MUST NOT（絶対にやらない／追加しない）:
  - 入力メッセージや token 使用量は Telegram に送らない（最終アウトプットのみ）。
  - token 等の機密情報を stdout/stderr/ログに出さない。
- OUT OF SCOPE:
  - topic の検索（既存発見）はしない（mapping が SSOT）。

## 境界（Always / Ask / Never） (必須)
- Always（常に守る）:
  - ローカル保存が SSOT（Telegram はベストエフォート）
- Ask（迷ったら相談）:
  - Telegram API 制約（topic 名/rate limit）
- Never（絶対にしない）:
  - `--telegram` 無しで送信する

## 非交渉制約（守るべき制約） (必須)
- 送信は最終アウトプットのみ（入力/トークン等は送らない）。
- 4096 文字制限に prefix を含めて収める（`adr-00007`）。

## 前提（Assumptions） (必須)
- Telegram は supergroup（topics 有効）が前提で、bot に topic 作成権限が付与されている。

## 判断材料/トレードオフ（Decision / Trade-offs） (任意)
- 論点: ...
  - 選択肢A: ...（Pros/Cons）
  - 選択肢B: ...（Pros/Cons）
  - 決定: ...
  - 理由: ...

## リスク/懸念（Risks） (任意)
- R-001: <リスク>（影響: ... / 対応: ...）
- R-002: ...

## 受け入れ条件（観測可能な振る舞い） (必須)
- AC-001:
  - Actor/Role: 利用者
  - Given: `--telegram` と必要 env が揃い、payload に `thread-id` と `last-assistant-message` がある
  - When: handler が実行される
  - Then: topic が作成/再利用され、最終アウトプットが投稿される
  - 観測点: Telegram / `telegram-topics.json`
- AC-002:
  - Actor/Role: 利用者
  - Given: `last-assistant-message` が 4096 文字を超える
  - When: 送信する
  - Then: 改行境界優先で分割され、各 chunk に `(i/n)` が付く
  - 観測点: Telegram 投稿
- AC-003:
  - Actor/Role: 利用者
  - Given: `--telegram` が無い
  - When: handler が実行される
  - Then: Telegram 送信を行わない
  - 観測点: Telegram に投稿されない / stderr
- AC-004:
  - Actor/Role: 利用者
  - Given: Telegram 送信が失敗する（429/network 等）
  - When: handler が実行される
  - Then: warn を出すが、ローカル保存が成功していれば exit 0
  - 観測点: stderr / exit code

### 入力→出力例 (任意)
- EX-001:
  - Input: ...
  - Output: ...
- EX-002:
  - Input: ...
  - Output: ...

## 例外・エッジケース（仕様として固定） (必須)
- EC-001:
  - 条件: `--telegram` だが env が不足
  - 期待: warn を出して送信しない（exit code はローカル保存の成否に従う）
  - 観測点: stderr
- EC-002:
  - 条件: payload に `thread-id` または `last-assistant-message` が無い（空文字も欠損扱い）
  - 期待: warn を出して送信しない（topic が作れない/本文が無い）
  - 観測点: stderr

## 用語（ドメイン語彙） (必須)
- TERM-001: topic = Telegram forum topics（`message_thread_id` で識別）
- TERM-002: mapping = `thread-id -> message_thread_id` の永続化（`.codex-log/telegram-topics.json`）

## 未確定事項（TBD / 要確認） (必須)
- 該当なし

## Definition of Ready（着手可能条件） (必須)
- [ ] 目的が 1〜3行で明確になっている
- [ ] MUST/MUST NOT/OUT OF SCOPE が書けている
- [ ] Always/Ask/Never が書けている
- [ ] AC/EC が観測可能（テスト可能）な形になっている
- [ ] 観測点（UI/HTTP/DB/Log など）または確認方法が明記されている
- [ ] 未確定事項が「質問/選択肢/推奨案/影響範囲」で整理されている

## 完了条件（Definition of Done） (必須)
- すべてのAC/ECが満たされる
- 未確定事項が解消される（残す場合は「残す理由」と「合意」を明記）
- MUST NOT / OUT OF SCOPE を破っていない

## 省略/例外メモ (必須)
- 該当なし
