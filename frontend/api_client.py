import json

import httpx


class RAGApiClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=300.0)

    def stream_chat(
        self, message, conversation_id=None, model=None, temperature=0.7, provider=None
    ):
        """Stream chat response via SSE. Yields (event_type, data_dict) tuples."""
        payload = {
            "message": message,
            "conversation_id": conversation_id,
            "model": model,
            "temperature": temperature,
            "provider": provider,
        }
        try:
            with self.client.stream(
                "POST", f"{self.base_url}/api/chat/stream", json=payload
            ) as response:
                current_event = "message"
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.strip()
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        if not data_str:
                            data = {}
                        else:
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                data = {"text": data_str, "token": data_str}
                        yield (current_event, data)
        except Exception as e:
            print(f"Error in stream_chat: {e}")
            yield ("error", {"detail": str(e)})

    def get_conversations(self) -> list[dict]:
        try:
            r = self.client.get(f"{self.base_url}/api/chat/conversations")
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []

    def create_conversation(self, title="New Chat") -> dict:
        try:
            r = self.client.post(
                f"{self.base_url}/api/chat/conversations", json={"title": title}
            )
            if r.status_code == 200:
                return r.json()
            return {}
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return {}

    def delete_conversation(self, conversation_id) -> bool:
        try:
            r = self.client.delete(
                f"{self.base_url}/api/chat/conversations/{conversation_id}"
            )
            return r.status_code == 200
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    def get_messages(self, conversation_id) -> list[dict]:
        try:
            r = self.client.get(
                f"{self.base_url}/api/chat/conversations/{conversation_id}/messages"
            )
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    def upload_document(
        self, file_name, file_bytes, content_type, conversation_id=None
    ) -> dict:
        try:
            files = {"file": (file_name, file_bytes, content_type)}
            data = {"conversation_id": conversation_id} if conversation_id else {}
            r = self.client.post(
                f"{self.base_url}/api/kb/upload", files=files, data=data
            )
            if r.status_code == 200:
                return r.json()
            return {}
        except Exception as e:
            print(f"Error uploading document: {e}")
            return {}

    def list_documents(self, conversation_id=None) -> list[dict]:
        try:
            params = {"conversation_id": conversation_id} if conversation_id else {}
            r = self.client.get(
                f"{self.base_url}/api/kb/documents", params=params
            )
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []

    def delete_document(self, document_id) -> bool:
        try:
            r = self.client.delete(f"{self.base_url}/api/kb/documents/{document_id}")
            return r.status_code == 200
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def get_analytics(self) -> dict:
        try:
            r = self.client.get(f"{self.base_url}/api/analytics/summary")
            if r.status_code == 200:
                return r.json()
            return {}
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}

    def health_check(self) -> bool:
        try:
            r = self.client.get(f"{self.base_url}/docs")
            return r.status_code == 200
        except Exception:
            return False
