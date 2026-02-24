---
種別: 実装報告書（Issue）
ID: "iss-00013"
タイトル: "Local direct runner script"
関連GitHub: ["#13"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00002", "init-00001"]
---

# iss-00013 Local direct runner script — 実装報告（LOG）

## 実装サマリー (任意)
- `scripts/codex-logger-dev` を追加し、ローカル clone の **ソースを直接実行**できるようにした（uvx のビルド/キャッシュに依存しない）。
- `notify = [...]` の設定例を README に追加し、開発/検証用途での導入手順を明確化した。

## 実装記録（セッションログ） (必須)

### 2026-02-24 24:10 - 24:20

#### 対象
- Step: S01, S03
- AC/EC: AC-001, AC-002, EC-001

#### 実施内容
- `scripts/codex-logger-dev` を追加し、`uv run --project <repo-root> --frozen python -m codex_logger.cli "$@"` を実行するようにした。
- 実行権限（`chmod +x`）が付与されることを担保した。
- smoke テストで `--help` と `--telegram + payload` の引数透過を検証した。

#### 実行コマンド / 結果
```bash
uv run --frozen pytest -q
# 結果: PASS（49 passed / exit code 0）
```

#### 変更したファイル
- `scripts/codex-logger-dev` - ローカル直接実行用の wrapper を追加
- `tests/test_dev_runner_script.py` - smoke テストを追加

#### コミット
- d4e6d08 feat(cli): ローカル直接実行スクリプトを追加

---

### 2026-02-24 24:20 - 24:25

#### 対象
- Step: S02
- AC/EC: AC-003

#### 実施内容
- README に `scripts/codex-logger-dev` の利用例と `notify` 設定例を追記した。

#### 変更したファイル
- `README.md` - ローカル直接実行の導線を追記

#### コミット
- 441d303 docs(readme): ローカル直接実行と診断ログを追記

---

## 遭遇した問題と解決 (任意)
- 問題: なし

## 学んだこと (任意)
- wrapper の引数透過は `"$@"` の誤りで簡単に壊れるため、実行を伴う smoke テストが有効。

## 今後の推奨事項 (任意)
- 開発/検証中は `scripts/codex-logger-dev`、通常運用は `uvx --from git+...@tag` を推奨。

## 省略/例外メモ (必須)
- 該当なし
