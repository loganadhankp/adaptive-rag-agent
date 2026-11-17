import json
import uuid
from datetime import datetime, timezone

from backend.database.connection import DatabaseManager


class ChatRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_conversation(
        self, id: str = None, title: str = "New Conversation"
    ) -> dict:
        conv_id = id or str(uuid.uuid4())
        now = self._now()
        with self.db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title, now, now),
            )
            conn.commit()
        return {
            "id": conv_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }

    def get_conversations(self) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, COUNT(m.id) as message_count 
                FROM conversations c 
                LEFT JOIN messages m ON c.id = m.conversation_id 
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_conversation(self, id: str) -> dict | None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM conversations WHERE id = ?", (id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_conversation(self, id: str) -> bool:
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_conversation_title(self, id: str, title: str):
        now = self._now()
        with self.db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, id),
            )
            conn.commit()

    def add_message(
        self,
        id: str = None,
        conversation_id: str = None,
        role: str = None,
        content: str = None,
        sources: list = None,
        workflow_metadata: dict = None,
    ) -> dict:
        msg_id = id or str(uuid.uuid4())
        now = self._now()
        if isinstance(content, list):
            content = "\n".join(str(c) for c in content)
        elif content is not None and not isinstance(content, str):
            content = str(content)
        sources_str = json.dumps(sources) if sources else None
        workflow_str = json.dumps(workflow_metadata) if workflow_metadata else None
        with self.db_manager.get_connection() as conn:
            conn.execute(
                (
                    "INSERT INTO messages (id, conversation_id, role, content, "
                    "sources, workflow_metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    msg_id,
                    conversation_id,
                    role,
                    content,
                    sources_str,
                    workflow_str,
                    now,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            conn.commit()
        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "sources": sources,
            "workflow_metadata": workflow_metadata,
            "created_at": now,
        }

    def get_messages(self, conversation_id: str) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                (
                    "SELECT * FROM messages WHERE conversation_id = ? "
                    "ORDER BY created_at ASC"
                ),
                (conversation_id,),
            )
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                msg["sources"] = (
                    json.loads(msg["sources"]) if msg.get("sources") else None
                )
                msg["workflow_metadata"] = (
                    json.loads(msg["workflow_metadata"])
                    if msg.get("workflow_metadata")
                    else None
                )
                messages.append(msg)
            return messages

    def log_analytics_event(
        self, conversation_id: str, event_type: str, event_data: dict = None
    ):
        event_id = str(uuid.uuid4())
        now = self._now()
        data_str = json.dumps(event_data) if event_data else None
        with self.db_manager.get_connection() as conn:
            conn.execute(
                (
                    "INSERT INTO analytics_events (id, conversation_id, event_type, "
                    "event_data, created_at) VALUES (?, ?, ?, ?, ?)"
                ),
                (event_id, conversation_id, event_type, data_str, now),
            )
            conn.commit()

    def get_analytics_summary(self) -> dict:
        with self.db_manager.get_connection() as conn:
            conv_count_row = conn.execute(
                "SELECT COUNT(id) FROM conversations"
            ).fetchone()
            msg_count_row = conn.execute("SELECT COUNT(id) FROM messages").fetchone()
            conv_count = conv_count_row[0] if conv_count_row else 0
            msg_count = msg_count_row[0] if msg_count_row else 0

            events = conn.execute(
                "SELECT event_type, event_data FROM analytics_events"
            ).fetchall()

            retrieval_success_count = sum(
                1 for e in events if e["event_type"] == "retrieval_success"
            )
            total_retrievals = sum(
                1
                for e in events
                if e["event_type"] in ("retrieval_success", "retrieval_failure")
            )
            success_rate = (
                (retrieval_success_count / total_retrievals) * 100
                if total_retrievals > 0
                else 100.0
            )

            rewrites_count = sum(
                1 for e in events if e["event_type"] == "query_rewrite"
            )
            web_searches = sum(1 for e in events if e["event_type"] == "web_search")
            hallucination_failures = sum(
                1 for e in events if e["event_type"] == "hallucination_failure"
            )

            quality_events = []
            for e in events:
                if e["event_type"] == "answer_quality" and e["event_data"]:
                    try:
                        d = json.loads(e["event_data"])
                        if isinstance(d, dict) and "score" in d:
                            quality_events.append(float(d["score"]))
                    except Exception:
                        pass
            avg_quality = (
                sum(quality_events) / len(quality_events) if quality_events else 0.0
            )

            return {
                "total_conversations": conv_count,
                "total_messages": msg_count,
                "total_queries": msg_count // 2 if msg_count > 0 else 0,
                "retrieval_success_rate": round(success_rate, 1),
                "query_rewrites_count": rewrites_count,
                "web_search_count": web_searches,
                "hallucination_failures_count": hallucination_failures,
                "avg_answer_quality": round(avg_quality, 1),
            }

    def add_document_record(
        self,
        id: str,
        filename: str,
        file_type: str,
        chunk_count: int,
        conversation_id: str | None = None,
    ) -> dict:
        doc_id = id or str(uuid.uuid4())
        now = self._now()
        with self.db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO documents (id, filename, file_type, chunk_count, uploaded_at, conversation_id) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, filename, file_type, chunk_count, now, conversation_id),
            )
            conn.commit()
        return {
            "id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "uploaded_at": now,
            "conversation_id": conversation_id,
        }

    def get_document(self, id: str) -> dict | None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_documents(self, conversation_id: str | None = None) -> list[dict]:
        with self.db_manager.get_connection() as conn:
            if conversation_id:
                cursor = conn.execute(
                    "SELECT * FROM documents WHERE conversation_id = ? ORDER BY uploaded_at DESC",
                    (conversation_id,),
                )
            else:
                cursor = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_document_record(self, id: str) -> bool:
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (id,))
            conn.commit()
            return cursor.rowcount > 0


Repository = ChatRepository
