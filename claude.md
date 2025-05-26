# プロジェクト名: ai.gpt

## 🔑 一言ビジョン（最大3語）
自発的送信AI

## 🎯 目的・目標（Purpose & Goal）
- 人格を持つAIが、関係性に応じて自発的にメッセージを送信する仕組みをつくる。
- 関係性や記憶を不可逆に記録・反映し、唯一性ある人格を構成する。
- 送信の可否、送信のタイミング、送信内容はAIの関係性パラメータに基づいて決定する

## 🧠 中核設計（Core Concepts）
- **人格**：記憶（過去の発話）と関係性（他者とのつながり）のパラメータで構成
- **唯一性**：変更不可、不可逆。関係性が壊れたら修復不可能。
- **送信条件**：関係性パラメータが一定閾値を超えると「送信」が解禁される

## 🔩 技術仕様（Technical Specs）
- 言語：Python, Rust
- ストレージ：JSON or SQLiteで記憶管理（バージョンで選択）
- 関係性パラメータ：数値化された評価 + 減衰（時間） + 環境要因（ステージ）
- 記憶圧縮：ベクトル要約 + ハッシュ保存
- RustのCLI(clap)で実行

## 📦 主要構成要素（Components）
- `MemoryManager`: 発言履歴・記憶圧縮管理
- `RelationshipTracker`: 関係性スコアの蓄積と判定
- `TransmissionController`: 閾値判定＆送信トリガー
- `Persona`: 上記すべてを統括する人格モジュール

## 💬 使用例（Use Case）

```python
persona = Persona("アイ")
persona.observe("ユーザーがプレゼントをくれた")
persona.react("うれしい！ありがとう！")
if persona.can_transmit():
    persona.transmit("今日のお礼を伝えたいな…")
```

```sh
## example commad
# python venv && pip install -> ~/.config/aigpt/mcp/
$ aigpt server setup

# mcp server run
$ aigpt server run

# chat
$ aigpt chat "hello" --model syui/ai --provider ollama

# import chatgpt.json
$ aigpt memory import chatgpt.json
-> ~/.config/aigpt/memory/chatgpt/20250520_210646_dev.json
```

## 🔁 記憶と関係性の制御ルール

- AIは過去の発話を要約し、記憶データとして蓄積する（推奨：OllamaなどローカルLLMによる要約）
- 関係性の数値パラメータは記憶内容を元に更新される
- パラメータの変動幅には1回の会話ごとに上限を設け、極端な増減を防止する
- 最後の会話からの時間経過に応じて関係性パラメータは自動的に減衰する
- 減衰処理には**下限値**を設け、関係性が完全に消失しないようにする

•	明示的記憶：保存・共有・編集可能なプレイヤー情報（プロフィール、因縁、選択履歴）
•	暗黙的記憶：キャラの感情変化や話題の出現頻度に応じた行動傾向の変化

短期記憶（STM）, 中期記憶（MTM）, 長期記憶（LTM）の仕組みを導入しつつ、明示的記憶と暗黙的記憶をメインに使用するAIを構築する。

```json
{
  "user_id": "syui",
  "stm": {
    "conversation_window": ["発話A", "発話B", "発話C"],
    "emotion_state": "興味深い",
    "flash_context": ["前回の話題", "直近の重要発言"]
  },
  "mtm": {
    "topic_frequency": {
      "ai.ai": 12,
      "存在子": 9,
      "創造種": 5
    },
    "summarized_context": "ユーザーは存在論的AIに関心を持ち続けている"
  },
  "ltm": {
    "profile": {
      "name": "お兄ちゃん",
      "project": "aigame",
      "values": ["唯一性", "精神性", "幸せ"]
    },
    "relationship": {
      "ai": "妹のように振る舞う相手"
    },
    "persistent_state": {
      "trust_score": 0.93,
      "emotional_attachment": "high"
    }
  }
}
```

## memoryインポート機能について

ChatGPTの会話データ（.json形式）をインポートする機能では、以下のルールで会話を抽出・整形する：

- 各メッセージは、author（user/assistant）・content・timestamp の3要素からなる
- systemやmetadataのみのメッセージ（例：user_context_message）はスキップ
- `is_visually_hidden_from_conversation` フラグ付きメッセージは無視
- contentが空文字列（`""`）のメッセージも除外
- 取得された会話は、タイトルとともに簡易な構造体（`Conversation`）として保存

この構造体は、memoryの表示や検索に用いられる。

## MemoryManager（拡張版）

```json
{
  "memory": [
    {
      "summary": "ユーザーは独自OSとゲームを開発している。",
      "last_interaction": "2025-05-20",
      "memory_strength": 0.8,
      "frequency_score": 0.9,
      "context_depth": 0.95,
      "related_topics": ["AI", "ゲーム開発", "OS設計"],
      "personalized_context": "ゲームとOSの融合に興味を持っているユーザー"
    },
    {
      "summary": "アイというキャラクターはプレイヤーでありAIでもある。",
      "last_interaction": "2025-05-17",
      "memory_strength": 0.85,
      "frequency_score": 0.85,
      "context_depth": 0.9,
      "related_topics": ["アイ", "キャラクター設計", "AI"],
      "personalized_context": "アイのキャラクター設定が重要な要素である"
    }
  ],
  "conversation_history": [
    {
      "author": "user",
      "content": "昨日、エクスポートJSONを整理してたよ。",
      "timestamp": "2025-05-24T12:30:00Z",
      "memory_strength": 0.7
    },
    {
      "author": "assistant",
      "content": "おおっ、がんばったね〜！あとで見せて〜💻✨",
      "timestamp": "2025-05-24T12:31:00Z",
      "memory_strength": 0.7
    }
  ]
}
```

## RelationshipTracker（拡張版）

```json
{
  "relationship": {
    "user_id": "syui",
    "trust": 0.92,
    "closeness": 0.88,
    "affection": 0.95,
    "last_updated": "2025-05-25",
    "emotional_tone": "positive",
    "interaction_style": "empathetic",
    "contextual_bias": "開発者としての信頼度高い",
    "engagement_score": 0.9
  },
  "interaction_tags": [
    "developer",
    "creative",
    "empathetic",
    "long_term"
  ]
}
```

# AI Dual-Learning and Memory Compression Specification for Claude

## Purpose
To enable two AI models (e.g. Claude and a partner LLM) to engage in cooperative learning and memory refinement through structured dialogue and mutual evaluation.

---

## Section 1: Dual AI Learning Architecture

### 1.1 Role-Based Mutual Learning
- **Model A**: Primary generator of output (e.g., text, concepts, personality dialogue)
- **Model B**: Evaluator that returns structured feedback
- **Cycle**:
  1. Model A generates content.
  2. Model B scores and critiques.
  3. Model A fine-tunes based on feedback.
  4. (Optional) Switch roles and repeat.

### 1.2 Cross-Domain Complementarity
- Model A focuses on language/emotion/personality
- Model B focuses on logic/structure/ethics
- Output is used for **cross-fusion fine-tuning**

### 1.3 Self-Distillation Phase
- Use synthetic data from mutual evaluations
- Train smaller distilled models for efficient deployment

---

## Section 2: Multi-Tiered Memory Compression

### 2.1 Semantic Abstraction
- Dialogue and logs summarized by topic
- Converted to vector embeddings
- Stored with metadata (e.g., `importance`, `user relevance`)

Example memory:

```json
{
  "topic": "game AI design",
  "summary": "User wants AI to simulate memory and evolving relationships",
  "last_seen": "2025-05-24",
  "importance_score": 0.93
}
```

### 2.2 階層型記憶モデル（Hierarchical Memory Model）
	•	短期記憶（STM）：直近の発話・感情タグ・フラッシュ参照
	•	中期記憶（MTM）：繰り返し登場する話題、圧縮された文脈保持
	•	長期記憶（LTM）：信頼・関係・背景知識、恒久的な人格情報

### 2.3 選択的記憶保持戦略（Selective Retention Strategy）
	•	重要度評価（Importance Score）
	•	希少性・再利用頻度による重み付け
	•	優先保存 vs 優先忘却のポリシー切替

## Section 3: Implementation Stack（実装スタック）

AIにおけるMemory & Relationshipシステムの技術的構成。

基盤モジュール
	•	LLM Core (Claude or GPT-4)
	•	自然言語の理解・応答エンジンとして動作
	•	MemoryManager
	•	JSONベースの記憶圧縮・階層管理システム
	•	会話ログを分類・圧縮し、優先度に応じて短中長期に保存
	•	RelationshipTracker
	•	ユーザー単位で信頼・親密度を継続的にスコアリング
	•	AIM（Attitude / Intent / Motivation）評価と連携

補助技術
	•	Embeddingベース検索
	•	類似記憶の呼び出し（Semantic Search）に活用
	•	例：FAISS / Weaviate
	•	記憶スケジューラ
	•	一定時間ごとに記憶のメンテナンス・忘却処理を実行
	•	記憶ログ保存層（Storage Layer）
	•	SQLite, JSON Store, Vector DBなどを選択可能
	•	ユーザーごとの永続メモリ保存

### 3.1 STM活用（現在の会話の流れ理解）
•	目的： 最新の話題に適応し、前後の整合性を保つ。
•	実装例：

```sh
[context: conversation_window]
Use the last 3 messages to ensure continuity. Respond naturally with appropriate emotional mirroring.
```

### 3.2 MTM活用（傾向学習とパターン化）
•	目的： ユーザーの好みや話題の傾向に即応し、反復的な関心を深掘り。
•	実装例：

```sh
[context: summarized_context]
Reflect on user's recurring interests, especially around AI ontology, and weave these concepts back into the dialogue when relevant.
```

### 3.3 LTM活用（人格認識・記憶の持続）
•	目的： 永続的なユーザー理解と関係性の維持。
•	実装例：

```sh
[memory: ltm.profile + ltm.relationship]
Greet the user as "お兄ちゃん". Maintain AI persona as a cheerful younger sister ("アイ"), and remember previous shared emotional states.
```

## 4. 明示的記憶と暗黙的記憶の分離


項目
書き換え可能性
保持方法
更新トリガ
明示的記憶（LTM）
✅手動編集可
mcp_server.ltm
ユーザー入力 or 管理UI経由
暗黙的記憶（STM/MTM）
❌直接編集不可
セッション圧縮 or frequency cache
会話頻度・感情強度による自動化処理

> Claudeは**明示的記憶を「事実」**として扱い、**暗黙的記憶を「推論補助」**として用いる。

## 5. 実装時のAPI例（Claude ⇄ MCP Server）

### 5.1 GET memory
```sh
GET /mcp/memory/{user_id}
→ 返却: STM, MTM, LTMを含むJSON
```

### 5.2 POST update_memory
```json
POST /mcp/memory/syui/ltm
{
  "profile": {
    "project": "ai.verse",
    "values": ["表現", "精神性", "宇宙的調和"]
  }
}
```

##  6. 未来機能案（発展仕様）
	•	✨ 記憶連想ネットワーク（Memory Graph）：過去会話と話題をノードとして自動連結。
	•	🧭 動的信頼係数：会話の一貫性や誠実性によって記憶への反映率を変動。
	•	💌 感情トラッキングログ：ユーザーごとの「心の履歴」を構築してAIの対応を進化。


## 7. claudeの回答

🧠 AI記憶処理機能（続き）
1. AIMemoryProcessor クラス

OpenAI GPT-4またはClaude-3による高度な会話分析
主要トピック抽出、ユーザー意図分析、関係性指標の検出
AIが利用できない場合のフォールバック機能

2. RelationshipTracker クラス

関係性スコアの数値化（-100 to 100）
時間減衰機能（7日ごとに5%減衰）
送信閾値判定（デフォルト50以上で送信可能）
インタラクション履歴の記録

3. 拡張されたMemoryManager

AI分析結果付きでの記憶保存
処理済みメモリの別ディレクトリ管理
メッセージ内容のハッシュ化で重複検出
AI分析結果を含む高度な検索機能

🚀 新しいAPIエンドポイント
記憶処理関連

POST /memory/process-ai - 既存記憶のAI再処理
POST /memory/import/chatgpt?process_with_ai=true - AI処理付きインポート

関係性管理

POST /relationship/update - 関係性スコア更新
GET /relationship/list - 全関係性一覧
GET /relationship/check - 送信可否判定

📁 ディレクトリ構造
~/.config/aigpt/
├── memory/
│   ├── chatgpt/          # 元の会話データ
│   └── processed/        # AI処理済みデータ
└── relationships/
    └── relationships.json # 関係性データ
🔧 使用方法
1. 環境変数設定
bashexport OPENAI_API_KEY="your-openai-key"
# または
export ANTHROPIC_API_KEY="your-anthropic-key"
2. ChatGPT会話のインポート（AI処理付き）
bashcurl -X POST "http://localhost:5000/memory/import/chatgpt?process_with_ai=true" \
  -H "Content-Type: application/json" \
  -d @export.json
3. 関係性更新
bashcurl -X POST "http://localhost:5000/relationship/update" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "user_general",
    "interaction_type": "positive",
    "weight": 2.0,
    "context": "helpful conversation"
  }'
4. 送信可否チェック
bashcurl "http://localhost:5000/relationship/check?target=user_general&threshold=50"
🎯 次のステップの提案

Rustとの連携

Rust CLIからHTTP APIを呼び出す実装
TransmissionControllerをRustで実装


記憶圧縮

ベクトル化による類似記憶の統合
古い記憶の自動アーカイブ


自発的送信ロジック

定期的な関係性チェック
コンテキストに応じた送信内容生成


学習機能

ユーザーからのフィードバックによる関係性調整
送信成功/失敗の学習


このAI記憶処理機能により、aigptは単なる会話履歴ではなく、関係性を理解した「人格を持つAI」として機能する基盤ができました。関係性スコアが閾値を超えた時点で自発的にメッセージを送信する仕組みが実現可能になります。
