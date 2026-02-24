---
種別: 実装報告書（Issue）
ID: "iss-00008"
タイトル: "Raw Payload Logging Files"
関連GitHub: ["#8"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00003", "init-00001"]
---

# iss-00008 Raw Payload Logging Files — 実装報告（LOG）

## 実装サマリー (任意)
- raw notify payload を改変せず `.codex-log/logs/*.json` に 1イベント=1ファイルで保存できるようにした。
- `O_EXCL` による排他的作成 + 衝突時のみ `__01`, `__02`... で上書きを回避し、欠損/不正JSONでも warn のみで保存を継続する。

## 実装記録（セッションログ） (必須)

### 2026-02-24 15:55 - 16:25

#### 対象
- Step: S01, S02, S03
- AC/EC: AC-001, AC-002, AC-003 / EC-001, EC-002, EC-003

#### 実施内容
- reviewer 事前レビューの指摘を反映し、衝突回避（EC-003）と permissions/exit code の契約を仕様に明記
- 欠落していた ADR-00010（raw JSON を SSOT とする決定）を追加
- `ids/timefmt/payload/log_store` を追加し、CLI から raw 保存を呼び出す実装を追加
- テストを追加し、AC/EC（+衝突/permissions/exit code）を担保
- 書き込み失敗時に不完全ログが残らないよう best-effort で削除（将来の summary 再生成ノイズを回避）

#### 実行コマンド / 結果
```bash
./spec-dock/scripts/spec-dock validate
spec-dock: ok (validate) nodes=14

uv run pytest -q
17 passed

uvx --from . codex-logger --help
# exit 0
```

#### 変更したファイル
- `spec-dock/active/issue/requirement.md` - EC-003追加 / Ask欄の確定反映
- `spec-dock/active/issue/design.md` - IF-LOG-001のエラー契約をADR-00008に整合
- `spec-dock/active/issue/plan.md` - 衝突/exit code/permissions のテスト計画を追加
- `spec-dock/initiatives/init-00001-codex-notify-json-logger/adrs/adr-00010-event-log-format-json-files.md` - raw JSON SSOT のADRを追加
- `src/codex_logger/cli.py` - payload parse→raw保存（失敗時は非0）
- `src/codex_logger/console.py` - warn/error の出力
- `src/codex_logger/ids.py` - event-id生成
- `src/codex_logger/timefmt.py` - `<ts>` 生成（UTC+ms）
- `src/codex_logger/payload.py` - best-effort parse（warn + fallback）
- `src/codex_logger/log_store.py` - `.codex-log/logs/*.json` へ排他的作成で保存
- `tests/test_cli_args.py` - 引数契約テスト（副作用はモック）
- `tests/test_log_store.py` - 保存/衝突/欠損/不正JSON/permissions をテスト
- `tests/test_cli_exit_codes.py` - 保存失敗時の非0をテスト

#### コミット
- （未）

#### メモ
- GitHub push が 403 のため、push/Issueクローズは認証修正後に実施する

---

### 2026-02-24 HH:MM - HH:MM

#### 対象
- Step: ...
- AC/EC: ...

#### 実施内容
- ...

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
