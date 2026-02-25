---
種別: 実装計画書（Issue）
ID: "iss-00014"
タイトル: "Summary chat transcript"
関連GitHub: ["#14"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-25"
依存: ["requirement.md", "design.md"]
親: ["epic-00003", "init-00001"]
---

# iss-00014 Summary chat transcript — 実装計画（TDD: Red → Green → Refactor）

## この計画で満たす要件ID (必須)
- 対象AC: AC-001, AC-002, AC-003
- 対象EC: EC-001, EC-002
- 対象制約:
  - 既存の lock + atomic replace を維持する（`rebuild_summary` の責務は変えない）
  - 依存追加なし

## ステップ一覧（観測可能な振る舞い） (必須)
- [ ] S01: `summary.md` に User/Assistant の本文が blockquote で出力され、`cwd` は出力されない
- [ ] S02: 欠損/型不正/空文字の本文が `<missing>` / `<invalid>` として best-effort で出力される
- [ ] S03: リファクタ + 全テスト通過 + report 更新（品質ゲート）

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

participant "summary renderer" as R
file "summary.md" as Sum

R -> Sum: "## <log file>\\n...\\n### User\\n> ...\\n\\n### Assistant\\n> ..."
@enduml
```

### 要件 ↔ ステップ対応表 (必須)
- AC-001 → S01
- AC-002 → S02
- AC-003 → S01
- EC-001 → S02（parse error の既存挙動を維持）
- EC-002 → S01
- 非交渉制約（lock + atomic replace） → S03（回帰テスト + 全体テスト）

---

## 実装ステップ（各ステップは“観測可能な振る舞い”を1つ） (必須)

### S01 — 本文（User/Assistant）を chat 形式で出力し、`cwd` を非表示化する (必須)
- 対象: AC-001, AC-003, EC-002
- 設計参照:
  - 対象IF: IF-SUM-002 / IF-SUM-003 / IF-SUM-004
  - 対象テスト:
    - `tests/test_summary.py::test_rebuild_summary_from_logs`
    - `tests/test_summary.py::test_multiline_messages_are_blockquoted`（追加）
- このステップで「追加しないこと（スコープ固定）」:
  - 欠損/型不正の placeholder 表示（S02 で扱う）

#### 期待する振る舞い（テストケース） (必須)
- Given: `logs/*.json` に `input-messages` と `last-assistant-message` を含むログがある
- When: `rebuild_summary(base_dir)` を実行する
- Then:
  - `summary.md` に `### User (i/n)` / `### Assistant` が出力される
  - 本文は `> ` で始まる行（blockquote）として出力される
  - 本文が複数行でも、すべての行が `> ` で prefix される
  - `cwd` が出力されない
- 観測点: `summary.md`
- 追加/更新するテスト: `tests/test_summary.py::test_rebuild_summary_from_logs`

#### Red（失敗するテストを先に書く） (任意)
- 期待する失敗: 現状は本文ブロックが存在せず、`cwd` が出力されるためテストが落ちる

#### Green（最小実装） (任意)
- 変更予定ファイル:
  - Modify: `src/codex_logger/summary.py`
  - Modify: `tests/test_summary.py`
- 追加する概念（このステップで導入する最小単位）:
  - blockquote 生成 helper（改行保持）
- 実装方針（最小で。余計な最適化は禁止）:
  - `render_summary` の出力を更新（本文ブロック追加 + `cwd` 非表示化）

#### Refactor（振る舞い不変で整理） (任意)
- 目的:
  - `render_summary` の見通しを上げ、出力フォーマットを明確化する
- 変更対象:
  - `src/codex_logger/summary.py`

#### ステップ末尾（省略しない） (必須)
- [ ] 期待するテスト（必要ならフォーマット/リンタ）を実行し、成功した
- [ ] コミットした（エージェント）

---

### S02 — 欠損/型不正の本文を best-effort で可視化する (必須)
- 対象: AC-002, EC-001
- 設計参照:
  - 対象IF: IF-SUM-003
  - 対象テスト: `tests/test_summary.py::test_missing_or_invalid_messages_are_rendered_best_effort`（追加）
- 期待する振る舞い:
  - `input-messages` が欠損/空配列なら `<missing>`、型不正なら `<invalid>` が表示される（要素が空文字の場合はその User ブロックが `<missing>`）
  - `last-assistant-message` が欠損/空文字なら `<missing>`、型不正なら `<invalid>` が表示される
  - JSON parse error は従来どおり `- parse error:` として記録される
- コマンド:
  - `uv run --frozen pytest -q tests/test_summary.py`
- ステップ末尾:
  - [ ] テストが通る
  - [ ] コミットした（エージェント）

---

### S03 — 仕上げ（リファクタ/全テスト/report） (必須)
- 対象: 非交渉制約（安全性/回帰）
- コマンド:
  - `uv run --frozen pytest -q`
  - `./spec validate`
- ステップ末尾:
  - [ ] 全テストが通る
  - [ ] `spec-dock/active/issue/report.md` を更新した
  - [ ] コミットした（エージェント）

---

## 未確定事項（TBD） (必須)
- 該当なし

## 完了条件（Definition of Done） (必須)
- 対象AC/ECがすべて満たされ、テストで保証されている
- MUST NOT / OUT OF SCOPE を破っていない
- 品質ゲート（フォーマット/リント/テストのうち該当するもの）が満たされている

## 省略/例外メモ (必須)
- 該当なし
