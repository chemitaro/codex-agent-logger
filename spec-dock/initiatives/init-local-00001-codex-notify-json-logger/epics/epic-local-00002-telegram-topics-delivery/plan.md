---
種別: 計画書（Epic）
ID: "epic-local-00002"
タイトル: "Telegram Topics Delivery"
関連GitHub: [""]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md"]
親: ["init-local-00001"]
---

# epic-local-00002 Telegram Topics Delivery — 計画（Issues / Order）

## Issue 分割（縦切り方針） (必須)
- 価値の縦切り（UI→API→DBまで通す） / 移行の縦切り（expand→...）:
  - 価値の縦切り: 「topic 作成/再利用」→「分割送信」→「mapping の原子的更新」
- 分割方針（原則）:
  - まずはモック API で検証し、実環境では env 設定時のみ有効化する
- 例外（分割方針を破る条件）:
  - なし（最小で進める）

## Issue 一覧（順序付き） (必須)
- iss-xxxx-... (MVP: topic 作成 + 最終アウトプット送信):
  - 目的:
    - `thread-id` 単位で topic を作成/再利用し、`last-assistant-message` を送信する
  - 成果物（Deliverable）:
    - `telegram-topics.json` の mapping 保存（ロック＋原子的置換）
    - 4096 超過時の分割送信（改行優先＋強制分割フォールバック）
    - `--telegram` 指定時のみ送信する（フラグ無しは送信しない）
    - `--telegram` 指定時に env 不足なら warn を出して送信しない
  - 対応する E-RQ / E-AC:
    - E-RQ-001..006 / E-AC-001..004
  - Depends on:
    - epic-local-00001（Local Logging and Summary）の log 保存（最後のアウトプット取得）
    - epic-local-00003（Packaging and CLI）の CLI 土台（pyproject/entrypoint/テスト基盤）

### UML（任意） (任意)
```plantuml
@startuml
skinparam monochrome true

rectangle "iss-... telegram topic+send" as I1
I1
@enduml
```

## 品質ゲート（Epic） (必須)
- [ ] 各 Issue が AC/EC を満たす自動テストを持つ（例外は理由がある）
- [ ] Epic の統合観点（E-AC）が確認できる（自動/半自動/手順のいずれか）
- [ ] 観測性（ログ/メトリクス/アラート）が入る（該当する場合）
- [ ] 移行手順/ロールバックが文書化される（該当する場合）

## ロールアウト / 移行 (必須)
- Feature flag:
  - `--telegram`（フラグ未指定なら送信しない）
- 段階公開（カナリア/一部テナント/内部先行など）:
  - なし（ローカル運用）
- ロールバック:
  - `--telegram` を外す（送信しない）

## Issue Definition of Ready（Issue に求める着手可能条件） (必須)
- [ ] Issue requirement に AC/EC がテスト可能な形で書けている
- [ ] Issue requirement に MUST/MUST NOT/OUT OF SCOPE と Always/Ask/Never がある
- [ ] Issue design に変更計画（パス単位）と要件→設計マッピングがある
- [ ] Issue design にテスト戦略（AC/EC→テスト）がある（該当なしの場合は理由がある）
- [ ] Issue plan が 1ステップ=1つの観測可能な振る舞いになっている
- [ ] 未確定事項が「質問/選択肢/推奨案/影響範囲」で整理されている

## 実行コマンド（必要なら） (任意)
- Test: `pytest -q`
- Lint/Format: `<command>`
- Typecheck: `<command>`

## 未確定事項（TBD） (必須)
- Q-001:
  - 質問: TBD ...
  - 選択肢:
    - A: ...
    - B: ...
  - 推奨案（暫定）:
    - ...
  - 影響範囲:
    - Issue分割 / 順序 / ロールアウト / 品質ゲート / ...

## 省略/例外メモ (必須)
- 該当なし
