# mcp/server.py
"""
Enhanced MCP Server with AI Memory Processing for aigpt CLI
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import aiohttp

# データモデル
class ChatMessage(BaseModel):
    message: str
    model: Optional[str] = None

class MemoryQuery(BaseModel):
    query: str
    limit: Optional[int] = 10

class ConversationImport(BaseModel):
    conversation_data: Dict[str, Any]

class MemorySummaryRequest(BaseModel):
    filepath: str
    ai_provider: Optional[str] = "openai"

class RelationshipUpdate(BaseModel):
    target: str  # 対象者/トピック
    interaction_type: str  # "positive", "negative", "neutral"
    weight: float = 1.0
    context: Optional[str] = None

# 設定
BASE_DIR = Path.home() / ".config" / "aigpt"
MEMORY_DIR = BASE_DIR / "memory"
CHATGPT_MEMORY_DIR = MEMORY_DIR / "chatgpt"
PROCESSED_MEMORY_DIR = MEMORY_DIR / "processed"
RELATIONSHIP_DIR = BASE_DIR / "relationships"

def init_directories():
    """必要なディレクトリを作成"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    CHATGPT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    RELATIONSHIP_DIR.mkdir(parents=True, exist_ok=True)

class AIMemoryProcessor:
    """AI記憶処理クラス"""
    
    def __init__(self):
        # AI APIの設定（環境変数から取得）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    async def generate_ai_summary(self, messages: List[Dict[str, Any]], provider: str = "openai") -> Dict[str, Any]:
        """AIを使用して会話の高度な要約と分析を生成"""
        
        # 会話内容を結合
        conversation_text = ""
        for msg in messages[-20:]:  # 最新20メッセージを使用
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {msg['content'][:500]}\n"
        
        # プロンプトを構築
        analysis_prompt = f"""
以下の会話を分析し、JSON形式で以下の情報を抽出してください：

1. main_topics: 主なトピック（最大5個）
2. user_intent: ユーザーの意図や目的
3. key_insights: 重要な洞察や学び（最大3個）
4. relationship_indicators: 関係性を示す要素
5. emotional_tone: 感情的なトーン
6. action_items: アクションアイテムや次のステップ
7. summary: 100文字以内の要約

会話内容:
{conversation_text}

回答はJSON形式のみで返してください。
"""
        
        try:
            if provider == "openai" and self.openai_api_key:
                return await self._call_openai_api(analysis_prompt)
            elif provider == "anthropic" and self.anthropic_api_key:
                return await self._call_anthropic_api(analysis_prompt)
            else:
                # フォールバック：基本的な分析
                return self._generate_basic_analysis(messages)
        except Exception as e:
            print(f"AI analysis failed: {e}")
            return self._generate_basic_analysis(messages)
    
    async def _call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """OpenAI APIを呼び出し"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            async with session.post("https://api.openai.com/v1/chat/completions", 
                                  headers=headers, json=data) as response:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
    
    async def _call_anthropic_api(self, prompt: str) -> Dict[str, Any]:
        """Anthropic APIを呼び出し"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            async with session.post("https://api.anthropic.com/v1/messages",
                                  headers=headers, json=data) as response:
                result = await response.json()
                content = result["content"][0]["text"]
                return json.loads(content)
    
    def _generate_basic_analysis(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基本的な分析（AI APIが利用できない場合のフォールバック）"""
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
        
        # キーワード抽出（簡易版）
        all_text = " ".join([msg["content"] for msg in messages])
        words = all_text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "main_topics": [word[0] for word in top_words],
            "user_intent": "情報収集・問題解決",
            "key_insights": ["基本的な会話分析"],
            "relationship_indicators": {
                "interaction_count": len(messages),
                "user_engagement": len(user_messages),
                "assistant_helpfulness": len(assistant_messages)
            },
            "emotional_tone": "neutral",
            "action_items": [],
            "summary": f"{len(user_messages)}回のやり取りによる会話"
        }

class RelationshipTracker:
    """関係性追跡クラス"""
    
    def __init__(self):
        init_directories()
        self.relationship_file = RELATIONSHIP_DIR / "relationships.json"
        self.relationships = self._load_relationships()
    
    def _load_relationships(self) -> Dict[str, Any]:
        """関係性データを読み込み"""
        if self.relationship_file.exists():
            with open(self.relationship_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"targets": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_relationships(self):
        """関係性データを保存"""
        self.relationships["last_updated"] = datetime.now().isoformat()
        with open(self.relationship_file, 'w', encoding='utf-8') as f:
            json.dump(self.relationships, f, ensure_ascii=False, indent=2)
    
    def update_relationship(self, target: str, interaction_type: str, weight: float = 1.0, context: str = None):
        """関係性を更新"""
        if target not in self.relationships["targets"]:
            self.relationships["targets"][target] = {
                "score": 0.0,
                "interactions": [],
                "created_at": datetime.now().isoformat(),
                "last_interaction": None
            }
        
        # スコア計算
        score_change = 0.0
        if interaction_type == "positive":
            score_change = weight * 1.0
        elif interaction_type == "negative":
            score_change = weight * -1.0
        
        # 時間減衰を適用
        self._apply_time_decay(target)
        
        # スコア更新
        current_score = self.relationships["targets"][target]["score"]
        new_score = current_score + score_change
        
        # スコアの範囲制限（-100 to 100）
        new_score = max(-100, min(100, new_score))
        
        self.relationships["targets"][target]["score"] = new_score
        self.relationships["targets"][target]["last_interaction"] = datetime.now().isoformat()
        
        # インタラクション履歴を追加
        interaction_record = {
            "type": interaction_type,
            "weight": weight,
            "score_change": score_change,
            "new_score": new_score,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        self.relationships["targets"][target]["interactions"].append(interaction_record)
        
        # 履歴は最新100件まで保持
        if len(self.relationships["targets"][target]["interactions"]) > 100:
            self.relationships["targets"][target]["interactions"] = \
                self.relationships["targets"][target]["interactions"][-100:]
        
        self._save_relationships()
        return new_score
    
    def _apply_time_decay(self, target: str):
        """時間減衰を適用"""
        target_data = self.relationships["targets"][target]
        last_interaction = target_data.get("last_interaction")
        
        if last_interaction:
            last_time = datetime.fromisoformat(last_interaction)
            now = datetime.now()
            days_passed = (now - last_time).days
            
            # 7日ごとに5%減衰
            if days_passed > 0:
                decay_factor = 0.95 ** (days_passed / 7)
                target_data["score"] *= decay_factor
    
    def get_relationship_score(self, target: str) -> float:
        """関係性スコアを取得"""
        if target in self.relationships["targets"]:
            self._apply_time_decay(target)
            return self.relationships["targets"][target]["score"]
        return 0.0
    
    def should_send_message(self, target: str, threshold: float = 50.0) -> bool:
        """メッセージ送信の可否を判定"""
        score = self.get_relationship_score(target)
        return score >= threshold
    
    def get_all_relationships(self) -> Dict[str, Any]:
        """すべての関係性を取得"""
        # 全ターゲットに時間減衰を適用
        for target in self.relationships["targets"]:
            self._apply_time_decay(target)
        
        return self.relationships

class MemoryManager:
    """記憶管理クラス（AI処理機能付き）"""
    
    def __init__(self):
        init_directories()
        self.ai_processor = AIMemoryProcessor()
        self.relationship_tracker = RelationshipTracker()
    
    def parse_chatgpt_conversation(self, conversation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ChatGPTの会話データを解析してメッセージを抽出"""
        messages = []
        mapping = conversation_data.get("mapping", {})
        
        # メッセージを時系列順に並べる
        message_nodes = []
        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue
            content = message.get("content", {})
            parts = content.get("parts", [])

            if parts and isinstance(parts[0], str) and parts[0].strip():
                message_nodes.append({
                    "id": node_id,
                    "create_time": message.get("create_time", 0),
                    "author_role": message["author"]["role"],
                    "content": parts[0],
                    "parent": node.get("parent")
                })
        
        # 作成時間でソート
        message_nodes.sort(key=lambda x: x["create_time"] or 0)
        
        for msg in message_nodes:
            if msg["author_role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["author_role"],
                    "content": msg["content"],
                    "timestamp": msg["create_time"],
                    "message_id": msg["id"]
                })
        
        return messages
    
    async def save_chatgpt_memory(self, conversation_data: Dict[str, Any], process_with_ai: bool = True) -> str:
        """ChatGPTの会話を記憶として保存（AI処理オプション付き）"""
        title = conversation_data.get("title", "untitled")
        create_time = conversation_data.get("create_time", datetime.now().timestamp())
        
        # メッセージを解析
        messages = self.parse_chatgpt_conversation(conversation_data)
        
        if not messages:
            raise ValueError("No valid messages found in conversation")
        
        # AI分析を実行
        ai_analysis = None
        if process_with_ai:
            try:
                ai_analysis = await self.ai_processor.generate_ai_summary(messages)
            except Exception as e:
                print(f"AI analysis failed: {e}")
        
        # 基本要約を生成
        basic_summary = self.generate_basic_summary(messages)
        
        # 保存データを作成
        memory_data = {
            "title": title,
            "source": "chatgpt",
            "import_time": datetime.now().isoformat(),
            "original_create_time": create_time,
            "messages": messages,
            "basic_summary": basic_summary,
            "ai_analysis": ai_analysis,
            "message_count": len(messages),
            "hash": self._generate_content_hash(messages)
        }
        
        # 関係性データを更新
        if ai_analysis and "relationship_indicators" in ai_analysis:
            interaction_count = ai_analysis["relationship_indicators"].get("interaction_count", 0)
            if interaction_count > 10:  # 長い会話は関係性にプラス
                self.relationship_tracker.update_relationship(
                    target="user_general",
                    interaction_type="positive",
                    weight=min(interaction_count / 10, 5.0),
                    context=f"Long conversation: {title}"
                )
        
        # ファイル名を生成
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.fromtimestamp(create_time).strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_title[:50]}.json"
        
        filepath = CHATGPT_MEMORY_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
        
        # 処理済みメモリディレクトリにも保存
        if ai_analysis:
            processed_filepath = PROCESSED_MEMORY_DIR / filename
            with open(processed_filepath, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def generate_basic_summary(self, messages: List[Dict[str, Any]]) -> str:
        """基本要約を生成"""
        if not messages:
            return "Empty conversation"
        
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
        
        summary = f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses. "
        
        if user_messages:
            first_user_msg = user_messages[0]["content"][:100]
            summary += f"Started with: {first_user_msg}..."
        
        return summary
    
    def _generate_content_hash(self, messages: List[Dict[str, Any]]) -> str:
        """メッセージ内容のハッシュを生成"""
        content = "".join([msg["content"] for msg in messages])
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def search_memories(self, query: str, limit: int = 10, use_ai_analysis: bool = True) -> List[Dict[str, Any]]:
        """記憶を検索（AI分析結果も含む）"""
        results = []
        
        # 処理済みメモリから検索
        search_dirs = [PROCESSED_MEMORY_DIR, CHATGPT_MEMORY_DIR] if use_ai_analysis else [CHATGPT_MEMORY_DIR]
        
        for search_dir in search_dirs:
            for filepath in search_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)
                    
                    # 検索対象テキストを構築
                    search_text = f"{memory_data.get('title', '')} {memory_data.get('basic_summary', '')}"
                    
                    # AI分析結果も検索対象に含める
                    if memory_data.get('ai_analysis'):
                        ai_analysis = memory_data['ai_analysis']
                        search_text += f" {' '.join(ai_analysis.get('main_topics', []))}"
                        search_text += f" {ai_analysis.get('summary', '')}"
                        search_text += f" {' '.join(ai_analysis.get('key_insights', []))}"
                    
                    # メッセージ内容も検索対象に含める
                    for msg in memory_data.get('messages', []):
                        search_text += f" {msg.get('content', '')}"
                    
                    if query.lower() in search_text.lower():
                        result = {
                            "filepath": str(filepath),
                            "title": memory_data.get("title"),
                            "basic_summary": memory_data.get("basic_summary"),
                            "source": memory_data.get("source"),
                            "import_time": memory_data.get("import_time"),
                            "message_count": len(memory_data.get("messages", [])),
                            "has_ai_analysis": bool(memory_data.get("ai_analysis"))
                        }
                        
                        if memory_data.get('ai_analysis'):
                            result["ai_summary"] = memory_data['ai_analysis'].get('summary', '')
                            result["main_topics"] = memory_data['ai_analysis'].get('main_topics', [])
                        
                        results.append(result)
                        
                        if len(results) >= limit:
                            break
                            
                except Exception as e:
                    print(f"Error reading memory file {filepath}: {e}")
                    continue
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_memory_detail(self, filepath: str) -> Dict[str, Any]:
        """記憶の詳細を取得"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Error reading memory file: {e}")
    
    def list_all_memories(self) -> List[Dict[str, Any]]:
        """すべての記憶をリスト"""
        memories = []
        
        for filepath in CHATGPT_MEMORY_DIR.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                memory_info = {
                    "filepath": str(filepath),
                    "title": memory_data.get("title"),
                    "basic_summary": memory_data.get("basic_summary"),
                    "source": memory_data.get("source"),
                    "import_time": memory_data.get("import_time"),
                    "message_count": len(memory_data.get("messages", [])),
                    "has_ai_analysis": bool(memory_data.get("ai_analysis"))
                }
                
                if memory_data.get('ai_analysis'):
                    memory_info["ai_summary"] = memory_data['ai_analysis'].get('summary', '')
                    memory_info["main_topics"] = memory_data['ai_analysis'].get('main_topics', [])
                
                memories.append(memory_info)
            except Exception as e:
                print(f"Error reading memory file {filepath}: {e}")
                continue
        
        # インポート時間でソート
        memories.sort(key=lambda x: x.get("import_time", ""), reverse=True)
        return memories

# FastAPI アプリケーション
app = FastAPI(title="AigptMCP Server with AI Memory", version="2.0.0")
memory_manager = MemoryManager()

@app.post("/memory/import/chatgpt")
async def import_chatgpt_conversation(data: ConversationImport, process_with_ai: bool = True):
    """ChatGPTの会話をインポート（AI処理オプション付き）"""
    try:
        filepath = await memory_manager.save_chatgpt_memory(data.conversation_data, process_with_ai)
        return {
            "success": True,
            "message": "Conversation imported successfully",
            "filepath": filepath,
            "ai_processed": process_with_ai
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/memory/process-ai")
async def process_memory_with_ai(data: MemorySummaryRequest):
    """既存の記憶をAIで再処理"""
    try:
        # 既存記憶を読み込み
        memory_data = memory_manager.get_memory_detail(data.filepath)
        
        # AI分析を実行
        ai_analysis = await memory_manager.ai_processor.generate_ai_summary(
            memory_data["messages"], 
            data.ai_provider
        )
        
        # データを更新
        memory_data["ai_analysis"] = ai_analysis
        memory_data["ai_processed_at"] = datetime.now().isoformat()
        
        # ファイルを更新
        with open(data.filepath, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
        
        # 処理済みディレクトリにもコピー
        processed_filepath = PROCESSED_MEMORY_DIR / Path(data.filepath).name
        with open(processed_filepath, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "Memory processed with AI successfully",
            "ai_analysis": ai_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search")
async def search_memories(query: MemoryQuery):
    """記憶を検索"""
    try:
        results = memory_manager.search_memories(query.query, query.limit)
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/list")
async def list_memories():
    """すべての記憶をリスト"""
    try:
        memories = memory_manager.list_all_memories()
        return {
            "success": True,
            "memories": memories,
            "count": len(memories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/detail")
async def get_memory_detail(filepath: str):
    """記憶の詳細を取得"""
    try:
        detail = memory_manager.get_memory_detail(filepath)
        return {
            "success": True,
            "memory": detail
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/relationship/update")
async def update_relationship(data: RelationshipUpdate):
    """関係性を更新"""
    try:
        new_score = memory_manager.relationship_tracker.update_relationship(
            data.target, data.interaction_type, data.weight, data.context
        )
        return {
            "success": True,
            "new_score": new_score,
            "can_send_message": memory_manager.relationship_tracker.should_send_message(data.target)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationship/list")
async def list_relationships():
    """すべての関係性をリスト"""
    try:
        relationships = memory_manager.relationship_tracker.get_all_relationships()
        return {
            "success": True,
            "relationships": relationships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relationship/check")
async def check_send_permission(target: str, threshold: float = 50.0):
    """メッセージ送信可否をチェック"""
    try:
        score = memory_manager.relationship_tracker.get_relationship_score(target)
        can_send = memory_manager.relationship_tracker.should_send_message(target, threshold)
        return {
            "success": True,
            "target": target,
            "score": score,
            "can_send_message": can_send,
            "threshold": threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(data: ChatMessage):
    """チャット機能（記憶と関係性を活用）"""
    try:
        # 関連する記憶を検索
        memories = memory_manager.search_memories(data.message, limit=3)
        
        # メモリのコンテキストを構築
        memory_context = ""
        if memories:
            memory_context = "\n# Related memories:\n"
            for memory in memories:
                memory_context += f"- {memory['title']}: {memory.get('ai_summary', memory.get('basic_summary', ''))}\n"
                if memory.get('main_topics'):
                    memory_context += f"  Topics: {', '.join(memory['main_topics'])}\n"
        
        # 関係性情報を取得
        relationships = memory_manager.relationship_tracker.get_all_relationships()
        
        # 実際のチャット処理
        enhanced_message = data.message
        if memory_context:
            enhanced_message = f"{data.message}\n\n{memory_context}"
        
        return {
            "success": True,
            "response": f"Enhanced response with memory context: {enhanced_message}",
            "memories_used": len(memories),
            "relationship_info": {
                "active_relationships": len(relationships.get("targets", {})),
                "can_initiate_conversations": sum(1 for target, data in relationships.get("targets", {}).items() 
                                                if memory_manager.relationship_tracker.should_send_message(target))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "service": "AigptMCP Server with AI Memory",
        "version": "2.0.0",
        "status": "running",
        "memory_dir": str(MEMORY_DIR),
        "features": [
            "AI-powered memory analysis",
            "Relationship tracking",
            "Advanced memory search",
            "Conversation import",
            "Auto-summary generation"
        ],
        "endpoints": [
            "/memory/import/chatgpt",
            "/memory/process-ai",
            "/memory/search",
            "/memory/list",
            "/memory/detail",
            "/relationship/update",
            "/relationship/list",
            "/relationship/check",
            "/chat"
        ]
    }

if __name__ == "__main__":
    print("🚀 AigptMCP Server with AI Memory starting...")
    print(f"📁 Memory directory: {MEMORY_DIR}")
    print(f"🧠 AI Memory processing: {'✅ Enabled' if os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY') else '❌ Disabled (no API keys)'}")
    uvicorn.run(app, host="127.0.0.1", port=5000)
