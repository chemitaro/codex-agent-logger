---
種別: 設計書（Issue）
ID: "iss-00011"
タイトル: "Gitignore codex log output"
関連GitHub: ["#11"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md"]
親: ["epic-00003", "init-00001"]
---

# iss-00011 Gitignore codex log output — 設計（HOW）

## 目的・制約（要件から転記・圧縮） (必須)
- 目的: `.codex-log/` の誤コミットを防ぐため、`codex-logger` 実行時に `<cwd>/.gitignore` を best-effort で更新する。
- MUST:
  - `<cwd>/.gitignore` に `.codex-log/` を追記（無ければ作成）し、重複追記しない。
  - `.gitignore` 更新失敗でもローカルログ保存は継続する（warning のみ）。
- MUST NOT:
  - `.gitignore` の削除/並び替え/全面上書き
  - `<cwd>` 以外の `.gitignore` 更新
- 非交渉制約:
  - 依存追加なし
  - ローカル保存は必達（`.gitignore` 失敗で exit non-zero にしない）
- 前提:
  - `.codex-log/` は `save_raw_payload` で作成される（epic-00003）

---

## 既存実装/規約の調査結果（As-Is / 99.9%理解） (必須)
- 参照した規約/実装（根拠）:
  - `AGENTS.md`: 出力先が `<cwd>/.codex-log/` であること、ローカル保存優先の方針
  - `src/codex_logger/log_store.py::save_raw_payload`: `.codex-log/` を作成して raw payload を保存する
  - `src/codex_logger/atomic.py::write_text_atomic`: 原子的ファイル置換ユーティリティ
- 観測した現状（事実）:
  - `.gitignore` は更新されないため、利用者が手動で `.codex-log/` を追加しないと誤コミットの余地がある。
- 採用するパターン（命名/責務/例外/DI/テストなど）:
  - `.gitignore` 更新は専用モジュールに切り出し、`log_store.save_raw_payload` から呼ぶ。
  - 追記は「必要なときだけ」行い、原子的に書き換える（tmp → replace）。
  - 失敗は warning に留め、例外は握りつぶす（ローカル保存優先）。
- 採用しない/変更しない（理由）:
  - `.git/info/exclude` や global gitignore は扱わない（OUT OF SCOPE）
- 影響範囲（呼び出し元/関連コンポーネント）:
  - `save_raw_payload` の実行時副作用（`.gitignore` 追記）

## 主要フロー（テキスト：AC単位で短く） (任意)
- Flow for AC-001:
  1) `.codex-log/` を作成する
  2) `.gitignore` が無ければ作成し、`.codex-log/` を書く
- Flow for AC-002:
  1) `.gitignore` を読む
  2) `.codex-log/` が無ければ追記して原子的に置換する

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true
hide footbox

participant "log_store.save_raw_payload" as Save
participant "gitignore.ensure_codex_log_ignored" as Ensure

Save -> Ensure: best-effort ensure\n(<cwd>/.gitignore)
Ensure --> Save: ok / warn only
@enduml
```

## データ・バリデーション（必要最小限） (任意)
- 該当なし（テキストファイルの追記のみ）

## 判断材料/トレードオフ（Decision / Trade-offs） (任意)
- 論点: `.gitignore` を更新失敗した場合の扱い
  - 決定: warning を出して継続（exit 0）
  - 理由: ローカルログ保存を最優先するため

## インターフェース契約（ここで固定） (任意)
### 関数・クラス境界（重要なものだけ）
- IF-001: `codex_logger.gitignore.ensure_codex_log_ignored(base_cwd: Path) -> bool`
  - Input: `<cwd>`（`.codex-log/` の親）
  - Output: 変更があれば True、変更無しなら False
  - Errors: 例外は投げず、warning を出して False を返す

## 変更計画（ファイルパス単位） (必須)
- 追加（Add）:
  - `src/codex_logger/gitignore.py`: `.gitignore` への `.codex-log/` 追記（best-effort / idempotent）
  - `tests/test_gitignore.py`: `.gitignore` 追記のユニットテスト
- 変更（Modify）:
  - `src/codex_logger/log_store.py`: raw 保存前後に `.gitignore` を best-effort 更新する
  - `tests/test_log_store.py`: `save_raw_payload` 経路での `.gitignore` 更新/失敗時継続を検証する
  - `README.md`: `.gitignore` の自動追記について補足する
- 削除（Delete）:
  - なし
- 移動/リネーム（Move/Rename）:
  - なし
- 参照（Read only / context）:
  - `src/codex_logger/atomic.py`: 原子的書き込みの再利用
  - `src/codex_logger/console.py`: warning 出力の整合

## マッピング（要件 → 設計） (必須)
- AC-001 → `gitignore.ensure_codex_log_ignored`（`.gitignore` が無い場合に作成）
- AC-002 → `gitignore.ensure_codex_log_ignored`（追記 / 重複防止）
- AC-003 → `gitignore.ensure_codex_log_ignored`（no-op）
- AC-004 → `gitignore.ensure_codex_log_ignored`（warning のみ、例外を投げない）
- AC-005 → `log_store._resolve_base_cwd` + `gitignore.ensure_codex_log_ignored`（payload の `cwd` を優先）
- EC-001/EC-002 → `gitignore.ensure_codex_log_ignored`（末尾改行 / 同等パターン検出）
- 非交渉制約 → `log_store.save_raw_payload`（`.gitignore` 失敗で処理を落とさない）

## テスト戦略（最低限ここまで具体化） (任意)
- 追加/更新するテスト:
  - Unit: `.gitignore` の作成/追記/重複防止/失敗時の扱い
- どのAC/ECをどのテストで保証するか:
- AC-001 → `tests/test_gitignore.py::test_ensure_creates_gitignore`
- AC-002 → `tests/test_gitignore.py::test_ensure_appends_once`
- AC-003 → `tests/test_gitignore.py::test_ensure_noop_when_present`
- AC-004 → `tests/test_log_store.py::test_save_raw_payload_warns_on_gitignore_failure_but_saves`
- AC-005 → `tests/test_log_store.py::test_save_raw_payload_updates_gitignore_in_payload_cwd_not_process_cwd`
- EC-001 → `tests/test_gitignore.py::test_ensure_appends_with_newline`
- EC-002 → `tests/test_gitignore.py::test_ensure_treats_equivalent_patterns_as_present`
- 実行コマンド:
  - `uv run --frozen pytest -q`

## リスク/懸念（Risks） (任意)
- R-001: <リスク>（影響: ... / 対応: ...）
- R-002: ...

## 未確定事項（TBD） (必須)
- 該当なし

---

## ディレクトリ/ファイル構成図（変更点の見取り図） (任意)
```text
<repo-root>/
├── README.md                          # Modify
├── src/
│   └── codex_logger/
│       ├── gitignore.py               # Add
│       └── log_store.py               # Modify
└── tests/
    ├── test_gitignore.py              # Add
    └── test_log_store.py              # Modify
```

## 省略/例外メモ (必須)
- 該当なし
