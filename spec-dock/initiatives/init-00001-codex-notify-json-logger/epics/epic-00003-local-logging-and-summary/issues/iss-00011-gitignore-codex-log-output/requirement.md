---
種別: 要件定義書（Issue）
ID: "iss-00011"
タイトル: "Gitignore codex log output"
関連GitHub: ["#11"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
親: ["epic-00003", "init-00001"]
---

# iss-00011 Gitignore codex log output — 要件定義（WHAT / WHY）

## 目的（ユーザーに見える成果 / To-Be） (必須)
- `codex-logger` 実行時に生成される `<cwd>/.codex-log/` 配下の全ファイルが、git 管理に入らない（誤コミットを避けられる）。
- 具体的には、`codex-logger` が **`<cwd>/.codex-log/.gitignore` を自動生成**し、`.codex-log/` 配下の全ディレクトリ/全ファイルを git 管理から外す（ignore する）。
- `.codex-log/` ディレクトリ外（例: `<cwd>/.gitignore`）は変更せず、プロジェクトの外部を汚染しない。

## 背景・現状（As-Is / 調査メモ） (必須)
- 現状の挙動（事実）:
  - `codex-logger` は `<cwd>/.codex-log/` を作成してログを書き込み、誤コミット防止のため `<cwd>/.gitignore` を更新している（現状）。
- 現状の課題（困っていること）:
  - プロジェクト直下の `<cwd>/.gitignore` を自動更新すると、利用者のリポジトリを汚染し得る（想定外の差分/レビュー負荷/方針違反）。
  - `.codex-log/` の ignore は **`.codex-log/` ディレクトリ内だけ**で完結させたい。
- 再現手順（最小で）:
  1) git 管理されているディレクトリで `codex-logger` を実行する
  2) `<cwd>/.gitignore` が変更される（現状）
- 観測点（どこを見て確認するか）:
  - filesystem: `<cwd>/.codex-log/.gitignore` の生成/内容、`<cwd>/.codex-log/` の生成
  - filesystem: `<cwd>/.gitignore` が変更されないこと
- 実際の観測結果（貼れる範囲で）:
  - Input/Operation: `codex-logger <payload-json>`
  - Output/State: `.codex-log/` とログが生成され、`<cwd>/.gitignore` が更新される（現状）
- 情報源（ヒアリング/調査の根拠）:
  - Issue/チケット: #11
  - コード: `src/codex_logger/log_store.py`（`save_raw_payload` が `.codex-log/` を作る）

## 対象ユーザー / 利用シナリオ (任意)
- 主な利用者（ロール）:
  - Codex CLI `notify` の handler として `codex-logger` を導入する開発者
- 代表的なシナリオ:
  - `codex-logger` 導入直後に `.gitignore` を追加し忘れても、ログが誤コミットされない

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

actor "Codex CLI" as Codex
participant "codex-logger" as Logger
database ".codex-log/" as Logs
file ".codex-log/.gitignore" as Gitignore

Codex -> Logger: notify(payload json)
Logger -> Logs: write logs/*.json\nrebuild summary.md
Logger -> Gitignore: ensure ignore-all\n(inside .codex-log only)
@enduml
```

## スコープ（暴走防止のガードレール） (必須)
- MUST（必ずやる）:
  - `codex-logger` 実行時、`<cwd>/.codex-log/.gitignore` を作成/更新し、`.codex-log/` 配下の全ディレクトリ/全ファイルを ignore する。
  - `.codex-log/.gitignore` の標準内容（少なくともこの内容を含む）:
    - `*`（`.codex-log/` 配下の全ファイル/全ディレクトリを ignore する）
  - `.codex-log/` ディレクトリ外（例: `<cwd>/.gitignore`）を変更しない。
  - `.codex-log/.gitignore` の更新に失敗しても、ローカルログ保存は継続する（warning を出す）。
- MUST NOT（絶対にやらない／追加しない）:
  - `<cwd>/.gitignore`（プロジェクト直下）を変更しない（追記/削除/並び替え/全面上書きを含む）。
  - `.codex-log/` の外に `.gitignore` を作成しない（親ディレクトリやホーム等も含む）。
  - `.codex-log/.gitignore` に機密値（token 等）を書かない。
- OUT OF SCOPE:
  - `.git/info/exclude` や global gitignore の操作
  - `.codex-log/` の自動削除/ローテーション

## 境界（Always / Ask / Never） (必須)
- Always（常に守る）:
  - `.codex-log/` の raw ログ保存（SSOT）を優先し、`.codex-log/.gitignore` 更新は best-effort とする
- Ask（迷ったら相談）:
  - `.codex-log/.gitignore` の内容（コメントを入れるか等）で迷った場合
- Never（絶対にしない）:
  - `<cwd>/.gitignore` の更新

## 非交渉制約（守るべき制約） (必須)
- 依存追加はしない（既存ユーティリティで実装する）。
- ローカル保存は必達（`.codex-log/.gitignore` の失敗で exit code を非0にしない）。

## 前提（Assumptions） (必須)
- `<cwd>` は書き込み可能である（少なくとも `.codex-log/` を作れる）。
- `.codex-log/.gitignore` を作成できる（失敗しても保存は継続する）。

## 判断材料/トレードオフ（Decision / Trade-offs） (任意)
- 論点: ignore の配置場所（`<cwd>/.gitignore` 更新 vs `.codex-log/.gitignore` 生成）
  - 決定: `.codex-log/.gitignore` を生成する（`.codex-log/` 内で完結）
  - 理由: 利用プロジェクト直下の `.gitignore` を変更せず、リポジトリ汚染を避けるため

## リスク/懸念（Risks） (任意)
- R-001: `.codex-log/.gitignore` が更新できない（影響: 誤コミットの可能性）
  - 対応: warning を出し、ログ保存は継続する

## 受け入れ条件（観測可能な振る舞い） (必須)
- AC-001:
  - Actor/Role: 開発者
  - Given: `<cwd>/.codex-log/.gitignore` が存在しない
  - When: `codex-logger` を実行する
  - Then: `<cwd>/.codex-log/.gitignore` が作成され、`.codex-log/` 配下を ignore するルールが含まれる
  - 観測点: filesystem
- AC-002:
  - Actor/Role: 開発者
  - Given: `<cwd>/.codex-log/.gitignore` が存在するが ignore-all ルールが無い、または内容が異なる
  - When: `codex-logger` を実行する
  - Then: `<cwd>/.codex-log/.gitignore` が標準の内容に更新される
  - 観測点: filesystem
- AC-003:
  - Actor/Role: 開発者
  - Given: `<cwd>/.gitignore` が存在する（内容は任意）
  - When: `codex-logger` を実行する
  - Then: `<cwd>/.gitignore` は変更されない（差分が出ない）
  - 観測点: filesystem
- AC-006:
  - Actor/Role: 開発者
  - Given: `<cwd>/.gitignore` が存在しない
  - When: `codex-logger` を実行する
  - Then: `<cwd>/.gitignore` は作成されない
  - 観測点: filesystem
- AC-004:
  - Actor/Role: 開発者
  - Given: `<cwd>/.codex-log/.gitignore` が更新できない（read-only 等）
  - When: `codex-logger` を実行する
  - Then: ローカルログ保存は成功し、stderr に warning が出る
  - 観測点: filesystem / stderr
- AC-005:
  - Actor/Role: 開発者
  - Given: payload の `cwd`（保存先）と、プロセスの実行時 `cwd` が異なる
  - When: `codex-logger` を実行する
  - Then: payload の `cwd` 側の `.codex-log/.gitignore` のみが作成/更新される（実行時 `cwd` 側は作成/更新しない）
  - 観測点: filesystem

### 入力→出力例 (任意)
- EX-001:
  - Input: `.codex-log/.gitignore` が無い状態で `codex-logger <payload>`
  - Output: `.codex-log/.gitignore` が作成される

## 例外・エッジケース（仕様として固定） (必須)
- EC-001:
  - 条件: `.codex-log/.gitignore` がディレクトリとして存在する等、ファイルを書けない
  - 期待: warning を出して継続し、ローカルログ保存は成功する
  - 観測点: filesystem
- EC-002:
  - 条件: `<cwd>/.codex-log/.gitignore` が既に存在するが内容が異なる
  - 期待: 標準の ignore-all ルール（`.codex-log/` 配下を全て ignore）に更新される
  - 観測点: filesystem
- EC-003:
  - 条件: `<cwd>/.codex-log/` がシンボリックリンク（symlink）である
  - 期待:
    - `.codex-log/.gitignore` の生成/更新をスキップし、warning を出して継続する（`<cwd>/.gitignore` を汚染しないため）
    - `.codex-log` symlink への `chmod` はスキップする（symlink のリンク先ディレクトリ権限を意図せず変更しないため）
  - 観測点: filesystem / stderr

## 用語（ドメイン語彙） (必須)
- TERM-001: `.codex-log/` = `codex-logger` が生成するログディレクトリ
- TERM-002: `.codex-log/.gitignore` = `.codex-log/` 配下を ignore するための gitignore ファイル

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
