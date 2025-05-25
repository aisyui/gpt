# chat_client.py
"""
Simple Chat Interface for AigptMCP Server
"""
import requests
import json
import os
from datetime import datetime

class AigptChatClient:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history = []
    
    def send_message(self, message: str) -> str:
        """メッセージを送信してレスポンスを取得"""
        try:
            # MCPサーバーにメッセージを送信
            response = requests.post(
                f"{self.server_url}/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "Sorry, no response received.")
                
                # 会話履歴を保存
                self.conversation_history.append({
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 関係性を更新（簡単な例）
                self.update_relationship(message, ai_response)
                
                return ai_response
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except requests.RequestException as e:
            return f"Connection error: {e}"
    
    def update_relationship(self, user_message: str, ai_response: str):
        """関係性を自動更新"""
        try:
            # 簡単な感情分析（実際はもっと高度に）
            positive_words = ["thank", "good", "great", "awesome", "love", "like", "helpful"]
            negative_words = ["bad", "terrible", "hate", "wrong", "stupid", "useless"]
            
            user_lower = user_message.lower()
            interaction_type = "neutral"
            weight = 1.0
            
            if any(word in user_lower for word in positive_words):
                interaction_type = "positive"
                weight = 2.0
            elif any(word in user_lower for word in negative_words):
                interaction_type = "negative"
                weight = 2.0
            
            # 関係性を更新
            requests.post(
                f"{self.server_url}/relationship/update",
                json={
                    "target": "user_general",
                    "interaction_type": interaction_type,
                    "weight": weight,
                    "context": f"Chat: {user_message[:50]}..."
                }
            )
        except:
            pass  # 関係性更新に失敗しても継続
    
    def search_memories(self, query: str) -> list:
        """記憶を検索"""
        try:
            response = requests.post(
                f"{self.server_url}/memory/search",
                json={"query": query, "limit": 5}
            )
            if response.status_code == 200:
                return response.json().get("results", [])
        except:
            pass
        return []
    
    def get_relationship_status(self) -> dict:
        """関係性ステータスを取得"""
        try:
            response = requests.get(f"{self.server_url}/relationship/check?target=user_general")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
    
    def save_conversation(self):
        """会話を保存"""
        if not self.conversation_history:
            return
        
        conversation_data = {
            "session_id": self.session_id,
            "start_time": self.conversation_history[0]["timestamp"],
            "end_time": self.conversation_history[-1]["timestamp"],
            "messages": self.conversation_history,
            "message_count": len(self.conversation_history)
        }
        
        filename = f"conversation_{self.session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Conversation saved to {filename}")

def main():
    """メインのチャットループ"""
    print("🤖 AigptMCP Chat Interface")
    print("Type 'quit' to exit, 'save' to save conversation, 'status' for relationship status")
    print("=" * 50)
    
    client = AigptChatClient()
    
    # サーバーの状態をチェック
    try:
        response = requests.get(client.server_url)
        if response.status_code == 200:
            print("✅ Connected to AigptMCP Server")
        else:
            print("❌ Failed to connect to server")
            return
    except:
        print("❌ Server not running. Please start with: python mcp/server.py")
        return
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                client.save_conversation()
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'save':
                client.save_conversation()
                continue
            elif user_input.lower() == 'status':
                status = client.get_relationship_status()
                if status:
                    print(f"📊 Relationship Score: {status.get('score', 0):.1f}")
                    print(f"📤 Can Send Messages: {'Yes' if status.get('can_send_message') else 'No'}")
                else:
                    print("❌ Failed to get relationship status")
                continue
            elif user_input.lower().startswith('search '):
                query = user_input[7:]  # Remove 'search '
                memories = client.search_memories(query)
                if memories:
                    print(f"🔍 Found {len(memories)} related memories:")
                    for memory in memories:
                        print(f"  - {memory['title']}: {memory.get('ai_summary', memory.get('basic_summary', ''))[:100]}...")
                else:
                    print("🔍 No related memories found")
                continue
            
            # 通常のチャット
            print("🤖 AI: ", end="", flush=True)
            response = client.send_message(user_input)
            print(response)
            
        except KeyboardInterrupt:
            client.save_conversation()
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
