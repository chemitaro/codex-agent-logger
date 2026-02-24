---
種別: ADR（Architecture Decision Record）
ID: "adr-00002"
タイトル: "Telegram topic naming"
状態: "draft"
作成者: "codex-agent"
最終更新: "2026-02-24"
親: ["init-local-00001"]
---

# adr-00002 Telegram topic naming（topic 名の命名規則）

## 結論（Decision） (必須)
- **未決（TBD）**: `thread-id`（セッション）ごとに作る Telegram topic の **topic 名**を決める。
- ステータス運用:
  - 結論が未決の間は `状態: draft`
  - 結論が確定したら `accepted`
- 決めたいこと:
  - topic 名の規則（Option A / B）
  - 例外時（長すぎる/禁則文字）の丸め方（上限超過時の短縮規則）
- 決定（決定後に記入）:
  - ...

## 背景（Context） (必須)
- 背景/制約（なぜ今決める必要があるか）:
  - `--telegram` 有効時、`thread-id` 単位で topic を作成/再利用するため、topic 名が運用上の「探しやすさ」を左右する。
  - topic の実体は `message_thread_id`（整数）で識別し、`thread-id -> message_thread_id` を `.codex-log/telegram-topics.json` に保存する。
    - つまり、topic 名は**UI のためのメタ情報**であり、正しさ（SoR）ではない。
  - ただし、人間が見て理解できない topic 名だと運用が破綻する。
- 前提:
  - Telegram は supergroup（forum topics 有効）を使用する。
  - topic の「検索」は行わず、mapping が SSOT（なければ新規作成）とする。
  - topic 名は Telegram の制約（長さ/改行等）に収まる必要がある。

### UML（命名生成の決定フロー）
```plantuml
@startuml
skinparam monochrome true

start
:thread-id;
:cwd;

if (Option A?) then (A)
  :topic = \"Codex \" + thread-id;
else (B)
  :prefix = repo_basename (if possible)\nelse cwd_basename;
  :topic = prefix + \" \" + thread-id;
endif

if (topic too long?) then (yes)
  :shorten thread-id;\n(keep uniqueness with hash if needed);
endif

stop
@enduml
```

## 選択肢（Options considered） (必須)
- Option A: `Codex <thread-id>`
  - 概要:
    - 固定プレフィックス `Codex` + `thread-id` のみ。
  - Pros:
    - 実装が最小（repo 推定不要）
    - topic 名の揺れが少ない
  - Cons:
    - topic 一覧で「どの作業（repo/cwd）のセッションか」が分かりにくい

- Option B: `<repo名> <thread-id>`（repo 不明時は `<cwd basename> <thread-id>`）
  - 概要:
    - `cwd` から repo 名（git repo root basename）を推定できる場合はそれを prefix にする。
    - 推定できない場合は `cwd` の basename を prefix にする。
  - Pros:
    - topic 一覧で探しやすい（コンテキストが見える）
    - 複数リポジトリを 1 つの supergroup で運用しやすい
  - Cons:
    - repo 推定ロジックが増える（ただし fallback 前提）

## 判断理由（Rationale） (必須)
- 判断軸:
  - 探しやすさ（topic 一覧での視認性）
  - 一意性（`thread-id` を含める）
  - 壊れにくさ（repo 推定に失敗しても cwd fallback で成立すること）
- 推奨案（暫定）:
  - Option B（repo 名 + thread-id / fallback to cwd basename）

## 影響（Consequences） (必須)
- Positive（良い点）:
  - Option B を採用すると、topic 一覧から目的のセッションに辿り着きやすい
- Negative / Debt（悪い点 / 将来負債）:
  - repo 推定不可のケースでは cwd prefix となり、運用上の揺れが残る
- 影響範囲（コード/テスト/運用/データ）:
  - `epic-local-00002` の topic 作成処理（topic name 生成）
  - テスト: topic 名の生成（repo/cwd fallback、長さ丸め）
- 移行/ロールバック:
  - 既存 mapping（`thread-id -> message_thread_id`）がある `thread-id` は topic ID を再利用できるため、命名規則の変更は「新規セッションの新規 topic」にのみ影響する
- Follow-ups（追加の Epic/Issue/ADR）:
  - 結論確定後、この ADR を `accepted` にし、`epic-local-00002` の requirement/design へ反映する

## 参考（References） (任意)
- 関連仕様（requirement/design/plan/report）:
  - `spec-dock/initiatives/init-local-00001-codex-notify-json-logger/requirement.md`
  - `spec-dock/initiatives/init-local-00001-codex-notify-json-logger/plan.md`
  - `spec-dock/initiatives/init-local-00001-codex-notify-json-logger/epics/epic-local-00002-telegram-topics-delivery/design.md`
- PR/実装:
  - （未実装）
- 外部資料:
  - Telegram Bot API（forum topics / sendMessage）
