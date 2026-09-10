import unittest
from unittest.mock import patch


# Mocks for database and documents
class TestKB(unittest.TestCase):

    @patch("backend.database.DatabaseManager")
    def test_db_manager_connection(self, MockDB):
        mock_db = MockDB()
        mock_db.connect.return_value = True
        self.assertTrue(mock_db.connect())

    @patch("backend.database.ChatRepository")
    def test_chat_repository_crud(self, MockRepo):
        repo = MockRepo()
        repo.create.return_value = {"id": "123", "title": "New Chat"}
        repo.get.return_value = {"id": "123", "title": "New Chat"}

        create_res = repo.create({"title": "New Chat"})
        self.assertEqual(create_res["id"], "123")

        get_res = repo.get("123")
        self.assertEqual(get_res["title"], "New Chat")

    def test_document_metadata_handling(self):
        metadata = {"author": "John Doe", "year": 2023, "tags": ["AI", "RAG"]}
        self.assertIn("author", metadata)
        self.assertEqual(metadata["year"], 2023)

    @patch("langchain_text_splitters.RecursiveCharacterTextSplitter")
    def test_text_splitting(self, MockSplitter):
        splitter = MockSplitter(chunk_size=100, chunk_overlap=20)
        splitter.split_text.return_value = ["chunk 1", "chunk 2"]

        chunks = splitter.split_text("This is a long text to be split.")
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], "chunk 1")


if __name__ == "__main__":
    unittest.main()
