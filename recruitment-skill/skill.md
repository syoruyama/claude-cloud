# スキル：人材紹介ワンストップワークフロー

## 概要

Geminiの文字起こしメール受信をトリガーに、議事録作成→求人検索→メール下書きまでを自動化するエージェント。
目標処理時間：**Slack確認応答後5分以内に完了**

---

## ツール構成

| ツール | 用途 |
|--------|------|
| Gmail | トリガー受信・メール下書き保存 |
| Google Sheets | 議事録URLの管理・ノウハウログ |
| Slack Bot | CAとのやり取り（条件確認・結果通知） |
| Circus（Playwright） | 求人検索・求人票ダウンロード |
| Claude API | 議事録生成・検索条件抽出・メール文章生成 |

---

## ワークフロー

```
[Gmail受信] Gemini文字起こし
    ↓
[STEP 1] 議事録生成 → Sheetsに記録
    ↓
[STEP 2] Slack Botが検索条件を提案 → CAが確認・修正
    ↓
[STEP 3] PlaywrightでCircus検索
    ↓ 3件未満 → 条件緩和して再検索
    ↓ 15件以上 → 条件絞って再検索
    ↓ 3〜14件 → スクショをSlackに返す
    ↓
[STEP 4] CAが企業名を返信
    ↓
[STEP 5] 求人票ダウンロード → メール下書き生成 → Slack完了通知
```

---

## STEP 1：議事録生成

### 入力
- Geminiからのメール本文（文字起こしテキスト）

### 処理
Claudeが文字起こしから以下を抽出・構造化：
- 候補者の基本情報（現職・年収・スキル）
- 転職理由・動機
- 希望条件（年収・職種・業界・勤務地・働き方）
- 懸念点・確認事項
- 次回アクション

### 出力
- 議事録をGoogle Docsに保存してURLを取得
- スプシの該当候補者行に議事録URLを貼り付け

---

## STEP 2：Slack Bot の検索条件提案

### 議事録から抽出する検索パラメータ（Circus対応10項目）

**基本条件（常に設定）**
| パラメータ | Circusの項目 | 例 |
|-----------|------------|-----|
| `keyword` | キーワード（AND条件） | 職種名・スキル名 |
| `job_category` | 職種 | エンジニア / PM / マーケティング |
| `location` | 勤務地 | 東京都 |
| `salary_min` | 下限年収（万円） | 800 |
| `salary_max` | 上限年収（万円） | 1200 |

**詳細条件（議事録の内容に応じて設定）**
| パラメータ | Circusの項目 | 値の選択肢 |
|-----------|------------|-----------|
| `industry` | 業種 | SaaS / FinTech / HRtech / AI / EC / ヘルステック 等 |
| `position_level` | 役位 | メンバー・一般 / シニア・スペシャリスト / マネージャー・リーダー / 部長・本部長 / 役員・C-suite |
| `remote_available` | リモートワーク | フルリモート可 / ハイブリッド / 出社必須 |
| `listing_status` | 上場区分 | 東証プライム / 東証スタンダード / 東証グロース / 未上場 / 外資系 |
| `employee_count` | 従業員数 | 〜100名 / 100〜500名 / 500〜2000名 / 2000名〜 |
| `employment_type` | 雇用形態 | 正社員 / 契約社員 / 業務委託 |
| `relocation_required` | 転勤の有無 | あり / なし |
| `overtime_max` | 残業時間上限（月） | 10 / 20 / 30 / 40 時間以内 |
| `education_requirement` | 学歴 | 不問 / 大卒以上 / 大学院卒以上 |
| `posted_within_days` | 求人更新日 | 7 / 30 / 90 日以内 |

### Slackメッセージ形式

```
📋 【○○様 面談後 求人検索条件】

以下の条件で検索します。確認・修正があればスレッドで返信してください。
問題なければ「OK」とご返信ください。

【基本条件】
・職種カテゴリ：エンジニアリングマネージャー
・勤務地：東京都
・年収：800万〜1,200万円

【詳細条件】
・業種：SaaS、FinTech
・役位：マネージャー・リーダー
・リモート：ハイブリッド以上
・上場区分：未上場〜東証グロース
・従業員数：100〜1,000名
・転勤：なし
・残業：月20時間以内
```

---

## STEP 3：Circus 求人検索（Playwright）

### 検索ロジック

```python
MAX_RETRIES = 3
TARGET_MIN = 3
TARGET_MAX = 14

def search_with_adjustment(params, attempt=0):
    results = circus_search(params)
    count = results["total"]

    if count < TARGET_MIN:
        # 条件緩和（優先順位順に1つずつ外す）
        relaxed = relax_conditions(params, attempt)
        return search_with_adjustment(relaxed, attempt + 1)

    elif count >= 15:
        # 条件強化（優先順位順に1つずつ追加・絞る）
        tightened = tighten_conditions(params, attempt)
        return search_with_adjustment(tightened, attempt + 1)

    else:
        # 3〜14件：スクショ取得してSlackに返す
        return results
```

### 条件の緩め方（優先順位順）

1. `posted_within_days` を 30日 → 90日に延ばす
2. `industry` を1〜2業種追加する
3. `employee_count` の範囲を広げる
4. `remote_available` の条件を外す
5. `overtime_max` の上限を引き上げる
6. `salary_max` を +100万円広げる

### 条件の絞り方（優先順位順）

1. `posted_within_days` を 90日 → 30日に縮める
2. `remote_available` を「フルリモート可」のみに絞る
3. `listing_status` を候補者好みの区分に絞る
4. `employee_count` の範囲を候補者希望に合わせて絞る
5. `overtime_max` の上限を引き下げる
6. `salary_min` を +50万円引き上げる

### Slack返信形式（3〜14件のとき）

```
✅ 【検索結果】○○様向け求人 — X件

確定検索条件：
・業種：SaaS、FinTech
・役位：マネージャー・リーダー
・年収：800万〜1,200万円
・リモート：ハイブリッド以上

[求人一覧スクリーンショット添付]

推薦したい企業があれば、企業名をスレッドで返信してください。
複数選択可です。
```

---

## STEP 4：求人票ダウンロード

- CAが返信した企業名からCircusで該当求人票を開く
- PDF or テキストとしてダウンロード
- 議事録テキストと求人票テキストをClaudeに渡す

---

## STEP 5：メール下書き生成

### 生成ルール

- **宛名**：候補者の氏名（敬称「様」）
- **書き出し**：面談のお礼（1〜2文）
- **推薦理由**：「なぜこの求人をこの人に勧めるか」を1〜2文で具体的に記述
  - 候補者の強み・希望と求人要件の一致点を明示
- **求人概要**：企業名・ポジション・年収レンジ
- **締め**：返信を促す一文（質問や次のステップの案内）
- **文字数**：400〜600文字（LINEコピペにも使いやすいサイズ）

### メール下書きの保存

- Gmailの下書きとして保存（送信はしない）
- 件名：`【ご紹介】○○株式会社 / ○○ポジション — [候補者名]様へ`

### Slack完了通知

```
🎉 【完了】○○様の求人提案フロー終了

・議事録：[Google Docs URL]
・Gmailに下書き保存済み（X社分）
・所要時間：約X分

下書きを確認して送信してください。
```

---

## ノウハウ蓄積（Sheetsへの自動ログ）

Slackのスレッドでやり取りした条件調整を自動でスプシに記録。

| 列 | 内容 |
|----|------|
| 日時 | タイムスタンプ |
| 候補者ID | C001 など |
| 候補者職種 | エンジニア / PM 等 |
| 初期条件 | 最初に提案した検索パラメータ（JSON） |
| 調整内容 | スレッドでの変更内容（テキスト） |
| 最終条件 | 検索確定時のパラメータ（JSON） |
| 結果件数 | 最終的な検索件数 |
| 採用された求人 | CAが選んだ企業名 |

これを蓄積することで、次回の同職種候補者への初期条件精度が向上する。

---

## Playwrightアダプター設計（保守性）

Circusの画面変更に対応しやすくするため、UI操作を1ファイルに集約する。

```
recruitment-skill/
└── agent/
    ├── circus_driver.py   ← UI操作はここだけ（保守対象）
    ├── claude_client.py   ← LLM処理
    ├── slack_bot.py       ← Slack連携
    ├── gmail_client.py    ← Gmail送受信・下書き
    └── sheets_client.py   ← スプシ読み書き
```

セレクタは可視テキストベースを優先（CSS classより壊れにくい）：

```python
# NG: CSS class依存（Circus更新で壊れやすい）
page.click(".search-btn-primary")

# OK: 表示テキスト依存（壊れにくい）
page.get_by_text("条件に合う求人を検索する").click()
page.get_by_label("下限年収").fill("800")
```

---

## 今後の拡張メモ

- [ ] 詳細検索条件（Circus実画面確認後に追加）
- [ ] 複数候補者の並列処理
- [ ] 推薦文（企業向け）の自動生成
- [ ] 求人充足・非公開チェック（再検索トリガー）
- [ ] ノウハウログからのfew-shot自動生成
