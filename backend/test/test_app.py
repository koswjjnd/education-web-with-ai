import pytest
from unittest.mock import Mock, patch
from flask import Flask, json
from app import app  # 导入 Flask 实例
from io import BytesIO
import pandas as pd

@pytest.fixture
def client():
    """ 创建 Flask 测试客户端 """
    app.config['Debug'] = True
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_file():
    """ 创建一个模拟 PDF 文件 """
    return BytesIO(b"Fake PDF content")

@pytest.fixture
def mock_genai():
    """ Mock `genai` 相关调用 """
    mock_genai_instance = MagicMock()
    
    # Mock `upload_file`
    mock_genai_instance.upload_file.return_value = "mock_uploaded_file"

    # Mock 生成模型
    mock_model = MagicMock()
    mock_model.generate_content.return_value = Mock(
        text=json.dumps({
            "lang": "English",
            "resource_type": "news",
            "title": "Mocked Title",
            "publish_time": "2024-10-25",
            "content": "Sample content."
        })
    ) 
    
    mock_genai_instance.GenerativeModel.return_value = mock_model
    mock_genai_instance.embed_content.return_value = {
        "embedding": [0.1] * 768 
    }
    return mock_genai_instance



from unittest.mock import MagicMock

@pytest.fixture
def mock_db():
    """ Mock 数据库连接 """
    mock_conn = MagicMock()  # 使用 MagicMock 代替 Mock
    mock_cursor = MagicMock()

    #让 `conn.cursor()` 返回 `mock_cursor`
    mock_conn.cursor.return_value = mock_cursor

    # 让 `with conn:` 和 `with conn.cursor():` 语句能正确执行
    mock_conn.__enter__.return_value = mock_conn  
    mock_conn.__exit__.return_value = None  
    mock_cursor.__enter__.return_value = mock_cursor  
    mock_cursor.__exit__.return_value = None  

    # 模拟 `fetchone()` 返回 article_id = 123
    mock_cursor.fetchone.return_value = [123]

    return mock_conn


def test_upload_and_process(client, mock_file, mock_db, mock_genai):
    """ 测试 `upload_and_process` API """

    with patch("app.create_connection", return_value=mock_db):
        with patch("app.genai", mock_genai):
            
            mock_genai.upload_file.return_value = "mock_uploaded_file"

            # Mock `genai.GenerativeModel`
            mock_model = Mock()
            mock_model.generate_content.return_value.text = """
            {"lang": "English", "resource_type": "news", "title": "Mocked Title", "publish_time": "2024-10-25", "content": "Sample content."}
            """
            mock_genai.GenerativeModel.return_value = mock_model

            # 发送 `multipart/form-data` 请求，模拟上传文件
            response = client.post("/upload", content_type="multipart/form-data",
                                   data={"file": (mock_file, "test.pdf")})

            response_data = response.get_json()

            print("Response Data:", response_data)

           
            assert response.status_code == 200
            assert response_data["status"] == "success"
            assert response_data["data"]["article_id"] == 123
            assert response_data["data"]["title"] == "Mocked Title"
            assert response_data["data"]["language"] == "English"
            assert response_data["data"]["publish_time"].startswith("2024-10-25")


@pytest.fixture
def mock_user_data_df():
    """ Mock user data DataFrame """
    return pd.DataFrame({
        "user_id": [12, 123],
        "age": [25, 30],
        "language": ["English", "Chinese"],
        "language_level": ["Beginner", "Intermediate"]
    })

@pytest.fixture
def mock_chat_store():
    """ Mock chat_store模拟查询用户聊天历史 """
    chat_store_mock = Mock()
    chat_store_mock.get_messages.return_value = [Mock(content="User's previous query")]
    return chat_store_mock

@pytest.fixture
def gemini_mock():
    """ Mock Gemini API 生成摘要 """
    class GeminiMock:
        def generate_content(self, prompt):
            return Mock(text="Mocked Summary of the articles")

    return GeminiMock()

@pytest.fixture
def mock_chat_memory_buffer(mock_chat_store):
    """ Mock ChatMemoryBuffer 并确保 chat_store 被 Mock """
    mock_memory_buffer = Mock()
    mock_memory_buffer.chat_store = mock_chat_store  # 这里确保 chat_store 也被 Mock
    return mock_memory_buffer

@pytest.fixture
def mock_embedding():
    """ Mock embedding model """
    embedding_mock = Mock()
    embedding_mock.get_text_embedding.return_value = [0.1, 0.2, 0.3]  # 假设返回向量
    return embedding_mock

@pytest.fixture
def mock_vector_store():
    """ Mock vector store query """
    vector_store_mock = Mock()
    mock_node_1 = Mock()
    mock_node_1.get_content.return_value = "First article content"
    mock_node_1.metadata = {"article_id": "A1"}
    mock_node_1.id_ = "1"
    mock_node_1.embedding = [0.1, 0.2, 0.3]

    mock_node_2 = Mock()
    mock_node_2.get_content.return_value = "Second article content"
    mock_node_2.metadata = {"article_id": "A2"}
    mock_node_2.id_ = "2"
    mock_node_2.embedding = [0.4, 0.5, 0.6]

    mock_node_3 = Mock()
    mock_node_3.get_content.return_value = "Third article content"
    mock_node_3.metadata = {"article_id": "A3"}
    mock_node_3.id_ = "3"
    mock_node_3.embedding = [0.7, 0.8, 0.9]

    vector_store_mock.query.return_value.nodes = [mock_node_1, mock_node_2, mock_node_3]
    return vector_store_mock
def test_article_recommendations_no_history(client, mock_chat_store, mock_chat_memory_buffer):
    
    with patch("app.chat_store", mock_chat_store):
        with patch("app.ChatMemoryBuffer.from_defaults", return_value=mock_chat_memory_buffer):
            mock_chat_store.get_messages.return_value = []  # 没有聊天记录

            test_request_data = {"user_id": 12}
            response = client.post('/article_recommendations', json=test_request_data)
            response_data = response.get_json()
            assert response.status_code == 404
            assert response_data["status"] == "error"
            assert response_data["message"] == "No queries found for this user"

def test_article_recommendations_success(client, mock_chat_store, mock_embedding, mock_vector_store, mock_chat_memory_buffer):
    """ 测试成功返回推荐的文章 """
    with patch("app.chat_store", mock_chat_store):
        with patch("app.ChatMemoryBuffer.from_defaults", return_value=mock_chat_memory_buffer):
            with patch("app.embedding_model", mock_embedding):
                with patch("app.vector_store", mock_vector_store):
                    
                    test_request_data = {"user_id": 12}
                    response = client.post('/article_recommendations', json=test_request_data)
                    response_data = response.get_json()
                    print(response_data)
                    
                    assert response.status_code == 200
                    assert response_data["status"] == "success"

                    # 确保返回的历史查询
                    assert "history" in response_data
                    assert response_data["history"] == ["User's previous query"]

                    # 确保返回的推荐文章
                    assert "results" in response_data
                    assert len(response_data["results"]) == 3
                    assert response_data["results"][0]["id"] == "1"
                    assert response_data["results"][0]["content"] == "First article content"
                    assert response_data["results"][0]["article_id"] == "A1"

def test_search_articles(client, gemini_mock, mock_embedding, mock_vector_store, mock_user_data_df):
    
    test_request_data = {
        "query": "AI News",
        "user_id":12
    }

    with patch("app.embedding_model", mock_embedding):
        with patch("app.vector_store", mock_vector_store):
            with patch("app.genai.GenerativeModel", return_value=gemini_mock):
                with patch("app.user_data_df", mock_user_data_df):
                    response = client.post('/search', json=test_request_data)
                    response_data = json.loads(response.data)

                    
                    assert response.status_code == 200
                    assert response_data["status"] == "success"

                    
                    assert "data" in response_data
                    assert len(response_data["data"]) == 3

                    
                    assert response_data["summary"].lstrip("> ").strip() == "Mocked Summary of the articles"

                    
                    assert "most_recommended" in response_data
                    assert "article_id" in response_data["most_recommended"]
                    assert "reason" in response_data["most_recommended"]
                
def test_search_articles_missing_query(client, mock_user_data_df):
   
    with patch("app.user_data_df", mock_user_data_df):
        test_request_data = {
        "user_id": 123
        }
        response = client.post('/search', json=test_request_data)
        response_data = response.get_json()
        
        # 应该返回 400 Bad Request
        assert response.status_code == 400
        assert response_data["status"] == "error"
        assert response_data["message"] == "Query is required"
