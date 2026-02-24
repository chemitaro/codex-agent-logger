---
種別: 実装報告書（Issue）
ID: "iss-00006"
タイトル: "README and Usage Examples"
関連GitHub: ["#6"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00006 README and Usage Examples — 実装報告（LOG）

## 実装サマリー (任意)
- `README.md` を追加し、uvx 実行例（GitHub / `@tag` / `@sha` / local）と Codex `notify` 統合例（Telegram なし/あり）を整備した。
- Telegram 前提（supergroup + topics、bot 権限）と env/.env 方針を明記し、機密値はプレースホルダに統一した。

## 実装記録（セッションログ） (必須)

### 2026-02-24 17:55 - 18:05

#### 対象
- Step: S01, S02
- AC/EC: AC-001, AC-002, AC-003, EC-001, EC-002

#### 実施内容
- `README.md` を新規作成し、uvx 実行例（GitHub / `@tag` / `@sha` / local path）を追加した。
- Codex CLI `notify` の設定例（Telegram なし/あり）を追加した。
- Telegram 利用前提（supergroup + topics、bot 権限、必要 env）を追記した。
- `.env` 方針（`<cwd>/.env` 自動読込、環境変数優先、`uvx --env-file` 任意）を追記した。
- `.codex-log/` の出力構成と参照先（spec-dock / ADR / notify docs）を追記した。
- 機密値はすべてプレースホルダ表記に統一した。

#### 実行コマンド / 結果
```bash
# N/A（ドキュメント変更のみ）
```

#### 変更したファイル
- `README.md` - README and Usage Examples の追加
- `spec-dock/active/issue/report.md` - iss-00006 セッションログ追記

#### コミット
- <hash> docs(readme): READMEと利用例を整備

#### メモ
- テスト: N/A（ドキュメント変更のみ）

---

## 遭遇した問題と解決 (任意)
- 問題: ...
  - 解決: ...

## 学んだこと (任意)
- ...
- ...

## 今後の推奨事項 (任意)
- ...
- ...

## 省略/例外メモ (必須)
- 該当なし
