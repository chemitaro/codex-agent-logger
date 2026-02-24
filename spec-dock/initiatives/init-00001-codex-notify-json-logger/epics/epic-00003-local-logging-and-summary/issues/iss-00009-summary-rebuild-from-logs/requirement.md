---
種別: 要件定義書（Issue）
ID: "iss-00009"
タイトル: "Summary Rebuild from Logs"
関連GitHub: ["#9"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
親: ["epic-00003", "init-00001"]
---

# iss-00009 Summary Rebuild from Logs — 要件定義（WHAT / WHY）

## 目的（ユーザーに見える成果 / To-Be） (必須)
- `.codex-log/logs/*.json`（SSOT）から `.codex-log/summary.md` を **毎回フル再生成**できる。
- 生成は `tmp -> atomic replace` で行い、失敗しても既存 summary を破損させない。

## 背景・現状（As-Is / 調査メモ） (必須)
- 現状の挙動（事実）:
  - raw 保存（`iss-00008`）の後に summary 再生成が無い。
- 現状の課題（困っていること）:
  - 人間は個別ログより summary を主に参照する。
  - 追記更新は事故が起きやすいので、毎回フル再生成したい。
- 観測点（どこを見て確認するか）:
  - FS: `.codex-log/summary.md` の生成と内容（時系列）
- 情報源（ヒアリング/調査の根拠）:
  - Initiative requirement/design（summary は毎回フレッシュ生成）

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

participant "codex-logger" as Handler
database "logs/*.json" as Logs
file "summary.md" as Sum

Handler -> Logs: scan (sorted)
Handler -> Handler: render markdown
Handler -> Sum: write summary.md.tmp
Handler -> Sum: atomic replace\n(os.replace)
@enduml
```

## スコープ（暴走防止のガードレール） (必須)
- MUST（必ずやる）:
  - `.codex-log/summary.md` を `logs/*.json` から **毎回フル再生成**する（追記は禁止）。
  - `summary.md.tmp` → `os.replace` の原子置換にする。
  - 同時実行でも破綻しない（ロック + 原子置換）。
  - JSON パース失敗が混ざっても summary 生成全体は失敗させない（エラーとして記録し継続）。
- MUST NOT（絶対にやらない／追加しない）:
  - `logs/*.json`（SSOT）を変更しない。
- OUT OF SCOPE:
  - Telegram 送信（`iss-00010`）

## 境界（Always / Ask / Never） (必須)
- Always（常に守る）:
  - summary は派生物であり、`logs/*.json` から再構成できる
- Ask（迷ったら相談）:
  - summary の出力フォーマット（読みやすさ vs 完全性）
- Never（絶対にしない）:
  - 追記更新（append）での summary 生成

## 非交渉制約（守るべき制約） (必須)
- summary は毎回フル再生成（append しない）。
- 失敗時に既存 `summary.md` を破損させない（tmp + 原子置換）。

## 前提（Assumptions） (必須)
- `logs/*.json` が SSOT として存在する（`iss-00008`）。

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
  - Actor/Role: 開発者
  - Given: `.codex-log/logs/*.json` が存在する
  - When: handler が実行される
  - Then: `.codex-log/summary.md` が生成され、ログが時系列で並ぶ
  - 観測点: FS / summary.md
- AC-002:
  - Actor/Role: 開発者
  - Given: 既存の `summary.md` がある
  - When: 再生成に失敗する（例: 書き込み不可）
  - Then: 既存 `summary.md` は保持される（破損しない）
  - 観測点: FS
- AC-003:
  - Actor/Role: 開発者
  - Given: JSON パースできないログが混ざる
  - When: summary を再生成する
  - Then: summary に parse error が記録され、他ログは継続して出力される
  - 観測点: summary.md

### 入力→出力例 (任意)
- EX-001:
  - Input: ...
  - Output: ...
- EX-002:
  - Input: ...
  - Output: ...

## 例外・エッジケース（仕様として固定） (必須)
- EC-001:
  - 条件: `logs/*.json` に不正 JSON がある
  - 期待: summary に parse error とファイル名を記録し、処理は継続
  - 観測点: summary.md
- EC-002:
  - 条件: 同時に複数の handler が走る
  - 期待: ロックにより summary が壊れない（最後に成功した出力が残る）
  - 観測点: summary.md / ロックファイル

## 用語（ドメイン語彙） (必須)
- TERM-001: summary = 個別ログ（SSOT）から生成される 1枚の Markdown
- TERM-002: atomic replace = `os.replace` による原子的なファイル差し替え

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
