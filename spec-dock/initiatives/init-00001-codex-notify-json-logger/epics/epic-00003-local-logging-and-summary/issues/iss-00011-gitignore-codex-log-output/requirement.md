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
- 具体的には、`codex-logger` が `<cwd>/.gitignore` に `.codex-log/` を確実に追加する（存在しない場合は作成する）。

## 背景・現状（As-Is / 調査メモ） (必須)
- 現状の挙動（事実）:
  - `codex-logger` は `<cwd>/.codex-log/` を作成してログを書き込むが、`<cwd>/.gitignore` は更新しない。
- 現状の課題（困っていること）:
  - 利用プロジェクト側で `.codex-log/` を `.gitignore` に入れ忘れると、`git status` に `.codex-log/` が表示され誤ってコミットされ得る。
- 再現手順（最小で）:
  1) git 管理されているディレクトリで `codex-logger` を実行し、`.codex-log/` を生成する
  2) `.gitignore` に `.codex-log/` が無い状態で `git status` を見る
- 観測点（どこを見て確認するか）:
  - filesystem: `<cwd>/.gitignore` の内容、`<cwd>/.codex-log/` の生成
  - git: `git status` の表示（`.codex-log/` が untracked として出ないこと）
- 実際の観測結果（貼れる範囲で）:
  - Input/Operation: `codex-logger <payload-json>`
  - Output/State: `.codex-log/` にログが作られるが `.gitignore` は更新されない（現状）
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
file ".gitignore" as Gitignore

Codex -> Logger: notify(payload json)
Logger -> Logs: write logs/*.json\nrebuild summary.md
Logger -> Gitignore: ensure '.codex-log/' is ignored
@enduml
```

## スコープ（暴走防止のガードレール） (必須)
- MUST（必ずやる）:
  - `codex-logger` 実行時、`<cwd>/.gitignore` に `.codex-log/` を追加する（無ければ作成する）。
  - 既存の `.gitignore` の内容を破壊しない（追記のみ / 重複追記しない）。
  - `.gitignore` の更新に失敗しても、ローカルログ保存は継続する（warning を出す）。
- MUST NOT（絶対にやらない／追加しない）:
  - `.gitignore` から既存行を削除/並び替えしない。
  - `<cwd>` 以外（親ディレクトリやホーム等）の `.gitignore` を変更しない。
  - `.gitignore` に機密値（token 等）を書かない。
- OUT OF SCOPE:
  - `.git/info/exclude` や global gitignore の操作
  - `.codex-log/` の自動削除/ローテーション

## 境界（Always / Ask / Never） (必須)
- Always（常に守る）:
  - `.codex-log/` の raw ログ保存（SSOT）を優先し、`.gitignore` 更新は best-effort とする
- Ask（迷ったら相談）:
  - `.gitignore` 追記形式（コメントを入れるか等）で迷った場合
- Never（絶対にしない）:
  - `.gitignore` の全面上書き

## 非交渉制約（守るべき制約） (必須)
- 依存追加はしない（既存ユーティリティで実装する）。
- ローカル保存は必達（`.gitignore` の失敗で exit code を非0にしない）。

## 前提（Assumptions） (必須)
- `<cwd>` は書き込み可能である（少なくとも `.codex-log/` を作れる）。
- `.gitignore` は UTF-8 テキストとして扱える（読めない場合は best-effort で諦める）。

## 判断材料/トレードオフ（Decision / Trade-offs） (任意)
- 論点: `.gitignore` を自動更新するか（手順を README に書くだけにするか）
  - 決定: 自動更新する（誤コミット防止を優先）
  - 理由: notify handler は自動で走るため、運用手順の抜け漏れを防ぐ価値が高い

## リスク/懸念（Risks） (任意)
- R-001: `.gitignore` が read-only で更新できない（影響: 誤コミットの可能性）
  - 対応: warning を出し、ログ保存は継続する

## 受け入れ条件（観測可能な振る舞い） (必須)
- AC-001:
  - Actor/Role: 開発者
  - Given: `<cwd>/.gitignore` が存在しない
  - When: `codex-logger` を実行する
  - Then: `<cwd>/.gitignore` が作成され、`.codex-log/` が含まれる
  - 観測点: filesystem
- AC-002:
  - Actor/Role: 開発者
  - Given: `<cwd>/.gitignore` が存在するが `.codex-log/` が含まれない
  - When: `codex-logger` を実行する
  - Then: `.gitignore` に `.codex-log/` が 1 回だけ追記される（重複しない）
  - 観測点: filesystem
- AC-003:
  - Actor/Role: 開発者
  - Given: `<cwd>/.gitignore` に `.codex-log/`（または同等の無視パターン）が既にある
  - When: `codex-logger` を実行する
  - Then: `.gitignore` は変更されない（差分が出ない）
  - 観測点: filesystem
- AC-004:
  - Actor/Role: 開発者
  - Given: `.gitignore` が更新できない（read-only 等）
  - When: `codex-logger` を実行する
  - Then: ローカルログ保存は成功し、stderr に warning が出る
  - 観測点: filesystem / stderr
- AC-005:
  - Actor/Role: 開発者
  - Given: payload の `cwd`（保存先）と、プロセスの実行時 `cwd` が異なる
  - When: `codex-logger` を実行する
  - Then: payload の `cwd` 側の `.gitignore` のみが更新される（実行時 `cwd` 側は更新しない）
  - 観測点: filesystem

### 入力→出力例 (任意)
- EX-001:
  - Input: `.gitignore` が無い状態で `codex-logger <payload>`
  - Output: `.gitignore` に `.codex-log/` が作成される

## 例外・エッジケース（仕様として固定） (必須)
- EC-001:
  - 条件: `.gitignore` の末尾が改行なし
  - 期待: `.codex-log/` は新しい行として追記され、末尾に改行が入る
  - 観測点: filesystem
- EC-002:
  - 条件: `.gitignore` に同等パターンが既に存在する
  - 同等パターン判定:
    - 行頭/行末の空白を trim した「行」が、次のいずれかに完全一致する（部分一致は禁止）:
      - `.codex-log/`
      - `.codex-log`
      - `/.codex-log/`
      - `/.codex-log`
    - コメント行（`# ...`）と空行は判定対象外（= 無視済みとは扱わない）
  - 期待: 追加追記しない（同等パターンとして扱う）
  - 観測点: filesystem

## 用語（ドメイン語彙） (必須)
- TERM-001: `.codex-log/` = `codex-logger` が生成するログディレクトリ
- TERM-002: `.gitignore` = git の無視ルールファイル

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
