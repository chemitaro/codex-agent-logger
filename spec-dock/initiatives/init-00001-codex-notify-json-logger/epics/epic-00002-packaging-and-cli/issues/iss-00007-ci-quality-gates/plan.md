---
種別: 実装計画書（Issue）
ID: "iss-00007"
タイトル: "CI Quality Gates"
関連GitHub: ["#7"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00007 CI Quality Gates — 実装計画（TDD: Red → Green → Refactor）

## この計画で満たす要件ID (必須)
- 対象AC: AC-001, AC-002, AC-003
- 対象EC: EC-001, EC-002
- 対象制約: Telegram secrets 不要で CI が通る（env 未設定でも成功する）

## ステップ一覧（観測可能な振る舞い） (必須)
- [ ] S01: GitHub Actions で pytest が実行される
- [ ] S02: GitHub Actions で `codex-logger --help` のスモークが実行される

### UML（任意） (任意)
```plantuml
@startuml
' TODO: 必要なら UML を追加する（形式は自由）
@enduml
```

### 要件 ↔ ステップ対応表 (必須)
- AC-001 → S01
- AC-002 → S02
- AC-003 → S01, S02
- EC-001 → S01
- EC-002 → S02

---

## 実装ステップ（各ステップは“観測可能な振る舞い”を1つ） (必須)

### S01 — GitHub Actions で pytest が実行される (必須)
- 対象: AC-001
- 設計参照:
  - 対象ファイル: `.github/workflows/ci.yml`
- このステップで「追加しないこと（スコープ固定）」:
  - デプロイや secrets 連携は行わない

#### update_plan（着手時に登録） (必須)
- [ ] `update_plan` に、このステップの作業ステップ（調査/Red/Green/Refactor/品質ゲート/報告/コミット）を登録した
- 登録例:
  - （調査）既存挙動/影響範囲の確認、設計参照の確認
  - （Red）失敗するテストの追加/修正
  - （Green）最小実装
  - （Refactor）整理
  - （品質ゲート）`uv run --frozen pytest -q` / `uvx --from . codex-logger --help`
  - （報告）`./spec-dock/active/issue/report.md` 更新
  - （コミット）このステップの区切りでコミット

#### 期待する振る舞い（テストケース） (必須)
- Given: PR/push
- When: workflow が走る
- Then: `uv run pytest -q` が実行される
- 観測点: GitHub Actions logs
- 追加/更新するテスト: N/A（CI 定義）

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

### S02 — GitHub Actions で `codex-logger --help` のスモークが実行される (必須)
- 対象: AC-001
- 設計参照:
  - `.github/workflows/ci.yml`
- 期待する振る舞い:
  - `uvx --from . codex-logger --help` が exit 0

---

## 未確定事項（TBD） (必須)
- 該当なし

## 完了条件（Definition of Done） (必須)
- 対象AC/ECがすべて満たされ、テストで保証されている
- MUST NOT / OUT OF SCOPE を破っていない
- 品質ゲート（フォーマット/リント/テストのうち該当するもの）が満たされている

## 省略/例外メモ (必須)
- 該当なし
