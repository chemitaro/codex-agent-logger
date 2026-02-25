---
種別: 実装報告書（Issue）
ID: "iss-00015"
タイトル: "Summary transcript v2"
関連GitHub: ["#15"]
状態: "approved"
作成者: "codex-agent"
最終更新: "2026-02-25"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00003", "init-00001"]
---

# iss-00015 Summary transcript v2 — 実装報告（LOG）

## 実装サマリー (任意)
- `summary.md` を transcript v2 として簡素化し、各ターンは「timestamp + last user + assistant」のみを表示するようにした。
- `type/turn-id/cwd/filename(event-id)` 等のノイズを排除し、`thread-id` は Assistant の括弧内だけに寄せた。

## 実装記録（セッションログ） (必須)

### 2026-02-25 10:05 - 10:46 UTC

#### 対象
- Step: S01, S02, S03
- AC/EC: AC-001..004 / EC-001..002

#### 実施内容
- `iss-00015` の要件/設計/計画を作成し、reviewer 指摘（thread-id 単独メタ行の抑止、timestamp 表示形式の固定）を反映して確定。
- `summary.md` の出力を v2 に更新（User は `input-messages` の最後の 1 要素のみ、Assistant は `last-assistant-message` のみ）。
- timestamp はファイル名プレフィックスを `YYYY-MM-DD HH:MM:SS.mmmZ` に整形して表示。
- reviewer 指摘により、`input-messages` の要素型不正（例: `["ok", 1]`）を `<invalid>` としてテストに追加し、回帰耐性を補強。

#### 実行コマンド / 結果
```bash
uv run --frozen pytest -q

51 passed

./spec validate

spec-dock: ok (validate) nodes=19
```

#### 変更したファイル
- `src/codex_logger/summary.py` - transcript v2 のレンダリング（timestamp + last user + assistant、ノイズ削除）
- `tests/test_summary.py` - v2 出力をテストで固定（last user のみ/メタ非表示/timestamp 形式）
- `spec-dock/active/issue/{requirement,design,plan}.md` - v2 仕様の確定

#### コミット
- ba45c86 chore(spec-dock): iss-00015 の雛形を追加
- 2735088 docs(spec-dock): iss-00015 の要件/設計/計画を追加
- 67b2ad2 feat(summary): transcript v2 に簡素化
- d5a2cdd test(summary): transcript v2 のinvalid判定を補強

#### メモ
- transcript v2 は「詳細は raw JSON（`logs/*.json`）を見る」前提で、summary の視認性を優先する。

---

## 遭遇した問題と解決 (任意)
- 問題: なし

## 学んだこと (任意)
- summary の UX は「情報量」より「ノイズ除去 + 1ターン=1往復」のほうが運用に効く

## 今後の推奨事項 (任意)
- 将来: transcript v1/v2 の切替（オプション）や、省略/折りたたみ等の改善を検討

## 省略/例外メモ (必須)
- 該当なし
