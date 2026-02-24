---
種別: 実装計画書（Issue）
ID: "iss-00006"
タイトル: "README and Usage Examples"
関連GitHub: ["#6"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00006 README and Usage Examples — 実装計画（TDD: Red → Green → Refactor）

## この計画で満たす要件ID (必須)
- 対象AC: AC-001, AC-002, AC-003
- 対象EC: EC-001, EC-002
- 対象制約: 機密情報を載せない / tag 固定推奨（`adr-00006`）

## ステップ一覧（観測可能な振る舞い） (必須)
- [ ] S01: README に uvx 実行例と notify 設定例が揃っている
- [ ] S02: README に Telegram 前提と env/.env 方針が揃っている

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true

rectangle "S01 usage examples" as S1
rectangle "S02 telegram/env notes" as S2

S1 --> S2
@enduml
```

### 要件 ↔ ステップ対応表 (必須)
- AC-001 → S01
- AC-002 → S01
- AC-003 → S02
- EC-001 → S02
- EC-002 → S02
- 非交渉制約（機密/タグ推奨）→ S02

---

## 実装ステップ（各ステップは“観測可能な振る舞い”を1つ） (必須)

### S01 — README に uvx 実行例と notify 設定例が揃っている (必須)
- 対象: AC-001, AC-002
- 設計参照:
  - 対象IF: IF-README-001
- このステップで「追加しないこと（スコープ固定）」:
  - 実装仕様の全文転記（spec-dock へリンクする）

#### update_plan（着手時に登録） (必須)
- [ ] `update_plan` に、このステップの作業ステップ（調査/Red/Green/Refactor/品質ゲート/報告/コミット）を登録した
- 登録例:
  - （調査）既存挙動/影響範囲の確認、設計参照の確認
  - （Red）失敗するテストの追加/修正
  - （Green）最小実装
  - （Refactor）整理
  - （品質ゲート）format/lint/test
  - （報告）`./spec-dock/active/issue/report.md` 更新
  - （コミット）このステップの区切りでコミット

#### 期待する振る舞い（テストケース） (必須)
- Given: README.md
- When: uvx 実行例と notify 設定例を読む
- Then: GitHub/tag/sha/local の uvx 例と、Telegram なし/ありの notify 例がある
- 観測点: `README.md`
- 追加/更新するテスト: N/A（ドキュメント）

#### Red（失敗するテストを先に書く） (任意)
- 期待する失敗:
  - ...

#### Green（最小実装） (任意)
- 変更予定ファイル:
  - Add: `<path/...>`
  - Modify: `<path/...>`
- 追加する概念（このステップで導入する最小単位）:
  - ...
- 実装方針（最小で。余計な最適化は禁止）:
  - ...

#### Refactor（振る舞い不変で整理） (任意)
- 目的:
  - ...
- 変更対象:
  - ...

#### ステップ末尾（省略しない） (必須)
- [ ] 期待するテスト（必要ならフォーマット/リンタ）を実行し、成功した
- [ ] `./spec-dock/active/issue/report.md` に実行コマンド/結果/変更ファイルを記録した
- [ ] `update_plan` を更新し、このステップの作業ステップを完了にした
- [ ] コミットした（エージェント）

---

### S02 — README に Telegram 前提と env/.env 方針が揃っている (必須)
- 対象: AC-003 / EC-001, EC-002
- 設計参照:
  - 対象IF: IF-README-001
- このステップで「追加しないこと（スコープ固定）」:
  - 機密値を例に含めない（プレースホルダのみ）

#### update_plan（着手時に登録） (必須)
- [ ] `update_plan` に、このステップの作業ステップ（調査/Red/Green/Refactor/品質ゲート/報告/コミット）を登録した

#### 期待する振る舞い（テストケース） (必須)
- Given: README.md
- When: Telegram 前提/環境変数/.env を読む
- Then: 必要 env、topics 前提、`.env` の優先順位（env > .env）が明記されている
- 観測点: `README.md`
- 追加/更新するテスト: N/A（ドキュメント）

---

## 未確定事項（TBD） (必須)
- 該当なし

## 完了条件（Definition of Done） (必須)
- 対象AC/ECがすべて満たされ、テストで保証されている
- MUST NOT / OUT OF SCOPE を破っていない
- 品質ゲート（フォーマット/リント/テストのうち該当するもの）が満たされている

## 省略/例外メモ (必須)
- 該当なし
