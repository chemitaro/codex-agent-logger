---
種別: 実装報告書（Issue）
ID: "iss-00009"
タイトル: "Summary Rebuild from Logs"
関連GitHub: ["#9"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00003", "init-00001"]
---

# iss-00009 Summary Rebuild from Logs — 実装報告（LOG）

## 実装サマリー (任意)
- `.codex-log/logs/*.json` を走査して `.codex-log/summary.md` を毎回フル再生成できるようにした（lock + tmp + atomic replace）。
- JSON パース失敗が混ざっても処理を継続し summary に記録する一方、summary の致命失敗（lock/atomic replace）は非0で検知できるようにした。

## 実装記録（セッションログ） (必須)

### 2026-02-24 16:40 - 17:15

#### 対象
- Step: S01, S02, S03
- AC/EC: AC-001, AC-002, AC-003 / EC-001, EC-002

#### 実施内容
- reviewer 指摘を反映し、base_dir の導出（`saved_path.parent.parent`）、exit code 契約、summary 最小フォーマットを仕様に固定
- `locks`（file lock）、`atomic`（tmp + `os.replace`）、`summary`（JSON→Markdown）を追加
- CLI を更新し、raw 保存（iss-00008）の後に summary 再生成を実行するようにした
- テストで順序/parse error 記録/旧summary保持/lock/exit code を担保

#### 実行コマンド / 結果
```bash
./spec-dock/scripts/spec-dock validate
spec-dock: ok (validate) nodes=14

uv run pytest -q
22 passed
```

#### 変更したファイル
- `spec-dock/active/issue/requirement.md` - 最小フォーマット/exit code 契約を追加
- `spec-dock/active/issue/design.md` - base_dir 導出規約を明記
- `spec-dock/active/issue/plan.md` - lock/exit code の具体テストを追加
- `src/codex_logger/atomic.py` - tmp + `os.replace` の原子書き込み
- `src/codex_logger/locks.py` - summary 用のファイルロック
- `src/codex_logger/summary.py` - `logs/*.json` → Markdown
- `src/codex_logger/cli.py` - raw 保存後に `summary.rebuild_summary(...)` を実行
- `tests/test_summary.py` - summary の順序/エラー/原子置換/lock
- `tests/test_cli_args.py` - summary 呼び出しをモック
- `tests/test_cli_exit_codes.py` - summary 再生成失敗時の非0
- `tests/test_log_store.py` - summary テストを分離

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
