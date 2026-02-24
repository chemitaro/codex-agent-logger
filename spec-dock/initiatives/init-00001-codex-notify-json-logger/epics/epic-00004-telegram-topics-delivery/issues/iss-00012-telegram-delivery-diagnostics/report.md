---
種別: 実装報告書（Issue）
ID: "iss-00012"
タイトル: "Telegram delivery diagnostics"
関連GitHub: ["#12"]
状態: "draft | approved"
作成者: "codex-agent"
最終更新: "2026-02-24"
依存: ["requirement.md", "design.md", "plan.md"]
親: ["epic-00004", "init-00001"]
---

# iss-00012 Telegram delivery diagnostics — 実装報告（LOG）

## 実装サマリー (任意)
- `--telegram` 指定時に Telegram 送信がスキップ/失敗した場合、`.codex-log/telegram-errors/<event>.md` に診断ログを best-effort で保存するようにした。
- env 不足時に Telegram API を呼ばないこと、診断ログが機密値や raw payload 全文を含まないことをテストで保証した。

## 実装記録（セッションログ） (必須)

### 2026-02-24 23:55 - 24:10

#### 対象
- Step: S01, S02, S03
- AC/EC: AC-001, AC-002, AC-003, AC-004, EC-001, EC-002, EC-003

#### 実施内容
- `telegram.send_last_message_best_effort` に `event_stem` を追加し、スキップ/失敗時に診断ログを出力するようにした。
- env 不足時は Telegram API を呼ばない（urlopen を呼ばない）ことをテストで保証した。
- API 失敗時・分割送信中の失敗時に、診断ログへ失敗要約と chunk i/n を残すようにした。
- 成功時は診断ログを生成しないようにした。

#### 実行コマンド / 結果
```bash
uv run --frozen pytest -q
# 結果: PASS（47 passed / exit code 0）
```

#### 変更したファイル
- `src/codex_logger/telegram.py` - スキップ/失敗時の診断ログ（best-effort）を追加
- `src/codex_logger/cli.py` - `event_stem`（saved_path.stem）を Telegram 送信へ渡す
- `tests/test_telegram_diagnostics.py` - 診断ログの生成/非生成、機密非出力、API未呼び出しを検証
- `tests/test_telegram_api_mock.py` - `event_stem` 追加に追随

#### コミット
- d2a9bc1 feat(telegram): 失敗/スキップ診断ログを追加

#### メモ
- 診断ログは `.codex-log/` 配下のみへ出力し、機密値（token 等）や raw payload 全文は出力しない。

---

## 遭遇した問題と解決 (任意)
- 問題: なし

## 学んだこと (任意)
- 失敗時の stderr だけだと運用上のデバッグが困難になるため、ファイル出力の観測点が有効。

## 今後の推奨事項 (任意)
- Telegram が届かない場合は、まず `.codex-log/telegram-errors/` を確認する。

## 省略/例外メモ (必須)
- 該当なし
