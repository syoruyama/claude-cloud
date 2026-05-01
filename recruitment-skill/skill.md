# スキル：人材紹介ワンストップワークフロー

## 概要

面談後の文字起こしデータを入力として、以下の一連業務を自動化するスキルです：

1. **議事録生成** — 文字起こしから構造化議事録を自動作成
2. **求人票マッチング** — 候補者プロフィールに最適な求人を検索・スコアリング
3. **チャットメッセージ下書き** — BizReachスタイルの候補者へのファーストメッセージを生成

---

## 使い方

### 基本コマンド

```
/recruitment-workflow [候補者名] [文字起こしファイルパス]
```

### 例

```
/recruitment-workflow 田中健一 ./data/transcripts/candidate_01.txt
```

---

## ワークフロー詳細

### STEP 1: 議事録生成

**入力**: 面談文字起こしテキスト

**処理**:
- 候補者の発言から「キャリア背景・強み・転職動機・希望条件」を抽出
- コンサルタントの質問と候補者の回答を構造化
- 懸念点・確認事項を整理
- 次回アクションを自動リストアップ

**出力形式** (Markdown):
```markdown
# 面談議事録

## 基本情報
- 候補者名：○○ 様
- 面談日：YYYY年MM月DD日
- 担当CA：○○コンサルタント

## 面談サマリー
...

## キャリア背景・強み
- ...

## 転職理由・動機
...

## 希望条件
- 年収：〜万円以上
- 職種：
- 業界：
- 勤務地：

## 懸念点・確認事項
- ...

## 求人マッチング方針
...

## 次回アクション
- [ ] ...
```

---

### STEP 2: 求人票マッチング

**入力**: 議事録から抽出した候補者プロフィール

**マッチングロジック**:

| スコア項目 | 重み |
|-----------|------|
| 職種カテゴリ一致 | 30% |
| 希望年収レンジ | 25% |
| 希望業界一致 | 20% |
| スキルセット合致 | 15% |
| 勤務地・働き方 | 10% |

**出力**: 上位5件の求人をスコア付きで表示

```
【マッチ度: ★★★★★】J001 - LayerX / エンジニアリングマネージャー
  年収: 900〜1,300万円 | 東京（リモート可）
  マッチ理由: Java/AWSスキル一致、チームリーダー経験を評価、年収レンジ合致

【マッチ度: ★★★★☆】J011 - Paidy / バックエンドエンジニア
  ...
```

---

### STEP 3: チャットメッセージ下書き

**入力**: 候補者プロフィール ＋ マッチした求人情報

**生成ルール**:
- BizReachの文体（丁寧かつフランクな敬語）
- 800文字以内（読みやすさ重視）
- 候補者の強みを1〜2点具体的に言及
- 紹介する求人を1〜2件ピックアップ（詳細は次のメッセージで）
- 返信しやすい終わり方（質問や確認依頼で締める）

**出力例**:
```
○○様

本日はお時間をいただき、ありがとうございました。
[強みへの具体的な言及]

早速ですが、○○様のご経験・ご志向に合致した求人をご紹介させてください。

【企業名 / ポジション名】
・年収：〜万円
・[特徴1行]

ご興味はいかがでしょうか？
ご都合のよいタイミングでお返事いただけますと幸いです。
```

---

## 実装メモ

### 使用データ

| ファイル | 説明 |
|---------|------|
| `data/candidates.json` | 10名の候補者プロフィール |
| `data/jobs.json` | 30件の求人票 |
| `data/transcripts/candidate_XX.txt` | 面談文字起こし |
| `data/minutes/candidate_XX.md` | 生成済み議事録 |
| `data/chats/candidate_XX.json` | チャット履歴 |

### デモ起動

```bash
# ローカルサーバーを起動（ブラウザで動作確認）
cd recruitment-skill/app
python3 -m http.server 8080
# → http://localhost:8080 を開く
```

### Claude APIを使った本番実装イメージ

```python
import anthropic

client = anthropic.Anthropic()

def generate_minutes(transcript: str) -> str:
    """文字起こしから議事録を生成"""
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        system="""あなたは人材紹介会社のCAアシスタントです。
        面談の文字起こしから構造化された議事録を作成してください。
        指定フォーマットに従い、日本語で出力してください。""",
        messages=[
            {
                "role": "user",
                "content": f"以下の文字起こしから議事録を作成してください:\n\n{transcript}"
            }
        ]
    )
    return response.content[0].text

def match_jobs(candidate_profile: dict, jobs: list) -> list:
    """候補者プロフィールに基づいて求人をマッチング・スコアリング"""
    profile_text = f"""
    職種: {candidate_profile['current_title']}
    希望年収: {candidate_profile['target_salary']}万円以上
    希望業界: {', '.join(candidate_profile['target_industries'])}
    スキル: {', '.join(candidate_profile['skills'])}
    転職動機: {candidate_profile['change_motivation']}
    """
    
    jobs_text = "\n".join([
        f"[{j['id']}] {j['company']} / {j['title']} "
        f"(年収{j['salary_min']}〜{j['salary_max']}万円, {j['industry']})"
        for j in jobs
    ])
    
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": f"""候補者プロフィール:\n{profile_text}\n\n求人一覧:\n{jobs_text}\n\n
                上記候補者に最適な求人を上位5件選び、各求人のマッチ理由を説明してください。"""
            }
        ]
    )
    return response.content[0].text

def draft_chat_message(candidate: dict, matched_jobs: list) -> str:
    """候補者へのチャットメッセージを下書き生成"""
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=800,
        system="""あなたは人材紹介会社のキャリアアドバイザーです。
        BizReachを通じて候補者に求人を紹介する丁寧なメッセージを作成してください。
        800文字以内で、候補者の強みを具体的に言及し、返信しやすい終わり方にしてください。""",
        messages=[
            {
                "role": "user", 
                "content": f"候補者: {candidate['name']}様\n強み: {', '.join(candidate['skills'][:3])}\n\nご紹介求人:\n{matched_jobs}"
            }
        ]
    )
    return response.content[0].text
```

---

## 拡張アイデア

- [ ] 複数候補者の一括処理
- [ ] 求人票の自動更新チェック（充足・非公開）
- [ ] 候補者の進捗管理（書類→面接→内定）自動トラッキング
- [ ] 推薦文自動生成（企業向け）
- [ ] 面談フィードバックのテンプレート生成
