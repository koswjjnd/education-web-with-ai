from flask import Flask, request, jsonify
import pg8000
from pg8000.dbapi import InterfaceError
import google.generativeai as genai
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import pathlib
import textwrap
import random
from IPython.display import display
from IPython.display import Markdown
import pandas as pd
from flask_cors import CORS
from datetime import datetime
import json
import re
import uuid  # 用于生成唯一标识符for request url in pinecone when upload pdf there is not url
import textstat
from werkzeug.utils import secure_filename
import os
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.storage.chat_store.postgres import PostgresChatStore
from llama_index.core.memory import ChatMemoryBuffer
from typing import List
from pydantic import BaseModel, Field
import asyncio
from llama_index.core.llms import ChatMessage
from llama_index.core.vector_stores.types import VectorStoreQuery
from flask_executor import Executor
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
executor = Executor(app)
CORS(app)


# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc=Pinecone(api_key=PINECONE_API_KEY)
index_name = "news-articles"


index = pc.Index(index_name)

num_users = 100
ages = [random.randint(18, 65) for _ in range(num_users)]
languages = ['English', 'Spanish', 'French', 'Chinese']
language_levels = ['Beginner', 'Intermediate', 'Advanced']

# Generate fake user data dataset
user_data = {
    "user_id": range(1, num_users + 1),
    "age": ages,
    "language": [random.choice(languages) for _ in range(num_users)],
    "language_level": [random.choice(language_levels) for _ in range(num_users)]
}
user_data_df = pd.DataFrame(user_data)
# Database connection setup
def create_connection():
    try:
        conn = pg8000.connect(
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT"))
        )
        return conn
    except InterfaceError as e:
        print(f"Error: Could not connect to the database. {e}")
        return None

@app.route('/')
def home():
    return jsonify({"message": "hello user"}) 


@app.route('/add', methods=['POST'])
def add():
    a = request.args.get('a')
    b = request.args.get('b')
    result = float(a) + float(b)

    return jsonify(result)

@app.route('/get_article', methods=['GET'])
def get_article():
    title = request.args.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    conn = create_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            query = """
            SELECT language, resource_type, title, publish_time, link, content 
            FROM test_table 
            WHERE title = %s
            """
            cursor.execute(query, (title,))
            result = cursor.fetchone()

            if result:
                response = {
                    'status': 'success',
                    'data': {
                        'language': result[0],
                        'resource_type': result[1],
                        'title': result[2],
                        'publish_time': result[3].isoformat(),
                        'link': result[4],
                        'content': result[5]
                    }
                }
                return jsonify(response), 200
            else:
                response = {
                    'status': 'error',
                    'message': 'Article not found'
                }
                return jsonify(response), 404

    finally:
        conn.close()
# 数据库查询函数
def fetch_article_details(article_id):
    conn = create_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        with conn.cursor() as cursor:
            # 查询文章详情
            query = """
            SELECT id, title, content, publish_time, language, resource_type
            FROM test_table
            WHERE id = %s
            """
            cursor.execute(query, (article_id,))
            result = cursor.fetchone()

            # 如果未找到记录
            if not result:
                return None

            # 映射到字典
            return {
                "id": result[0],
                "title": result[1],
                "content": result[2],
                "publish_time": result[3],
                "language": result[4],
                "resource_type": result[5],
            }
    finally:
        conn.close()
@app.route('/article/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    article = fetch_article_details(article_id)
    if not article:
            
        return jsonify({
                "status": "error",
                "message": f"Article with ID {article_id} not found"
        }), 404

        
    return jsonify({
            "status": "success",
            "data": article
        }), 200

@app.route('/articles/counts', methods=['GET'])
def get_article_counts():
    
    conn = create_connection()
    if conn is None:
        # 数据库连接失败
        return jsonify({
            "status": "error",
            "message": "Database connection failed"
        }), 500

    try:
        with conn.cursor() as cursor:
            # 查询文章总数
            query = "SELECT COUNT(*) FROM test_table"
            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                # 成功返回文章数量
                return jsonify({
                    "status": "success",
                    "data": {
                        "article_counts": result[0]
                    }
                }), 200
            else:
                # 查询结果为空
                return jsonify({
                    "status": "error",
                    "message": "Could not count articles"
                }), 500
    finally:
        conn.close()

@app.route('/update_article', methods=['PUT'])
def update_article():
    title = request.args.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    conn = create_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            # Step 1: Get the current article data
            select_query = """
            SELECT id, language, resource_type, title, publish_time, link
            FROM test_table
            WHERE title = %s
            """
            cursor.execute(select_query, (title,))
            current_data = cursor.fetchone()

            if not current_data:
                return jsonify({'error': 'Article not found'}), 404

            article_id = current_data[0]
            # Step 2: Compare and prepare the fields to be updated
            update_fields = {}
            for idx, field in enumerate(['language', 'resource_type', 'title', 'publish_time', 'link'], start=1):
                new_value = request.json.get(field)
                if new_value and new_value != current_data[idx]:
                    update_fields[field] = new_value

            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400

            set_clause = ', '.join([f"{key} = %s" for key in update_fields.keys()])
            values = list(update_fields.values())
            values.append(article_id)

            # Step 3: Update the article using the ID
            update_query = f"UPDATE test_table SET {set_clause} WHERE id = %s"
            cursor.execute(update_query, values)
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({'status': 'success','message': 'Article updated successfully'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Article not found'}), 404
    finally:
        conn.close()

@app.route('/delete_article', methods=['DELETE'])
def delete_article():

    title = request.args.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    conn = create_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            delete_query = "DELETE FROM test_table WHERE title = %s"
            cursor.execute(delete_query, (title,))
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({'status': 'success','message': 'Article deleted successfully'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Article not found'}), 204
    finally:
        conn.close()
def to_markdown(text):
    # Replacing bullet points with asterisks for Markdown-like lists
    text = text.replace('•', '*')
    # Indenting the text to simulate blockquote formatting
    indented_text = textwrap.indent(text, '> ', predicate=lambda _: True)
    return indented_text


genai.configure(api_key=GOOGLE_API_KEY)

class GeminiFlashEmbedding(BaseEmbedding):
    """
    子类化 BaseEmbedding实现抽象方法并扩展功能
    """
    api_key: str = Field(..., description="API key for accessing the GenAI service.")
    model_name: str = Field(default="gemini-flash-embedding", description="Model name for embeddings.")

    def __init__(self, api_key: str, model_name: str = "gemini-flash-embedding"):
        # Initialize Pydantic fields and validate input
        super().__init__(api_key=api_key, model_name=model_name)

    def _get_query_embedding(self, query: str) -> List[float]:
        """同步获取查询嵌入向量"""
        embedding_result = genai.embed_content(
            model=self.model_name,
            content=query,
            task_type="retrieval_query"
        )
        return embedding_result['embedding']

    async def _aget_query_embedding(self, query: str) -> List[float]:
        """异步获取查询嵌入向量"""
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        """同步获取文本嵌入向量"""
        embedding_result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document"
        )
        return embedding_result['embedding']

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """同步批量获取文本嵌入向量"""
        return [self._get_text_embedding(text) for text in texts]

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """异步获取文本嵌入向量"""
        return self._get_text_embedding(text)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """异步批量获取文本嵌入向量"""
        return await asyncio.gather(*[self._aget_text_embedding(text) for text in texts])

embedding_model = GeminiFlashEmbedding(
        api_key=GOOGLE_API_KEY,
        model_name="models/text-embedding-004"
    )

vector_store = PineconeVectorStore(
    pinecone_index=index,
    embedding=embedding_model,
    text_key="content"
)

def get_postgres_uri():
    """Generate a PostgreSQL URI using environment variables."""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME")

    # 构造 PostgreSQL URI
    return f"postgresql+pg8000://{user}:{password}@{host}:{port}/{database}"

# Initialize PostgresChatStore
chat_store = PostgresChatStore.from_uri(
    uri=get_postgres_uri(),
)
@app.route('/search', methods=['POST'])
def search_articles():
    data = request.json
    query = data.get('query')
    user_id = data.get('user_id')

    # Fetch user data from the simulated dataset
    user_row = user_data_df[user_data_df['user_id'] == user_id]

    if user_row.empty:
        return jsonify({'status': 'error','message': f'User ID {user_id} not found'}), 404

    # Extract user's language and language level
    user_language = user_row.iloc[0]['language']
    user_language_level = user_row.iloc[0]['language_level']
    if not query:
        return jsonify({'status': 'error','message': 'Query is required'}), 400
    
    try:
    # 创建或检索用户的 chat memory
        user_chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=3000,
            chat_store=chat_store,
            chat_store_key=f"user_{user_id}",  # 唯一用户 key
        )

        
        new_message = ChatMessage(role="user", content=query)  # 创建新消息
        executor.submit(async_put_message, user_chat_memory, new_message)  # 后台运行省时间 免得浪费整个function的时间 也不用返回它相关的东西 you can call async put, because your critical path doesnt' depend on the results of the chat history
        print('Message added to chat memory')

    except Exception as e:
        print(f"Error occurred: {e}")

    # # Generate embedding for the query
    # embedding_result = genai.embed_content(
    #     model="models/text-embedding-004",
    #     content=query,
    #     task_type="retrieval_document"
    # )
    # query_embedding = embedding_result['embedding']

    # # Search for similar articles in Pinecone
    # search_results = index.query(
    #     vector=query_embedding,
    #     top_k=3,
    #     include_metadata=True
    # )
    # Generate embedding for the query
    query_embedding = embedding_model.get_text_embedding(query)

    vector_query = VectorStoreQuery(
        query_embedding=query_embedding,  # 嵌入向量
        similarity_top_k=3  # 返回前 3 个结果
    )

    # 调用查询
    search_results = vector_store.query(query=vector_query)
    # 假设 search_results.nodes 是 BaseNode 对象的列表
    articles = []

    for node in search_results.nodes:
        # 提取元数据
        content = node.get_content()
        article_id = node.metadata.get('article_id', 'Unknown')

        # 提取节点 ID 和嵌入向量
        node_id = node.id_
        embedding = node.embedding

        # 可读性分数
        readability_score = textstat.flesch_reading_ease(content)

        # 构建结果
        articles.append({
            'id': node_id,
            'content': content,
            'article_id': article_id,
            'embedding': embedding,
            'readability_score': readability_score
        })
        

    prompt_template = f"""
There is one combined news content. I want you to summarize the following news content, limit it to 200 words, and start with:
"Here is a summary in {user_language} for a user with {user_language_level} proficiency:"

Example:
Combined Content: "Microsoft announces a new AI model for enterprise use, promising to revolutionize productivity in the workplace. The model integrates seamlessly with existing Microsoft 365 applications and provides advanced features like predictive text and task automation. Meanwhile, Google has rolled out a significant update to its search algorithm, designed to improve relevance and user experience by prioritizing high-quality content and penalizing clickbait. The update is expected to impact millions of websites globally. Additionally, Apple unveiled its latest MacBook Pro equipped with the groundbreaking M3 chip. The device boasts a 30% increase in performance and twice the battery life compared to its predecessor. It is targeted at professionals requiring high computational power, such as video editors and software developers. This wave of innovation highlights the fierce competition among tech giants to dominate the enterprise and consumer markets."
Combined Summary: "Here is a summary in English for a user with Advanced proficiency: Microsoft’s new AI model enhances productivity through integration with Microsoft 365, while Google’s updated search algorithm improves content relevance globally. Apple’s M3 MacBook Pro offers unprecedented performance and battery life, catering to professional users. These developments reflect the ongoing competition among major tech companies."

Now, summarize this article:
{{content}}
"""
    # define model for generating summaries
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Combine all the articles' content into one string
    combined_content = " ".join(article['content'] for article in articles)
    print(f"Combined content: {combined_content}")
    # Fill in the template values using the combined news content
    combined_prompt = prompt_template.format(content=combined_content)
    result = model.generate_content(combined_prompt)
    summary=to_markdown(result.text)
    articles_id = [article['article_id'] for article in articles]
    articles_sorted = sorted(articles, key=lambda x: x['readability_score'], reverse=True)

    # Determine the most recommended article based on user_language_level
    most_recommended_article_id = None
    if user_language_level.lower() == 'beginner':
        most_recommended_article_id = articles_sorted[0]['article_id']  # Highest readability score
    elif user_language_level.lower() == 'intermediate':
        most_recommended_article_id = articles_sorted[1]['article_id']
    elif user_language_level.lower() == 'advanced':
        most_recommended_article_id = articles_sorted[2]['article_id']
    response_data = {
    'status': 'success',
    'data': articles_id,
    'summary': summary
    }

    # Include the most recommended article for beginners if applicable
    if most_recommended_article_id:
        response_data['most_recommended'] = {
            'article_id': most_recommended_article_id,
            'reason': 'Most suitable news based on your language level'
        }
    
    return jsonify(response_data), 200

async def async_put_message(user_chat_memory, new_message):
    try:
        await asyncio.sleep(0)  # Simulates an async operation
        user_chat_memory.put(new_message)  # This operation is now backgrounded
    except Exception as e:
        print(f"Async operation failed: {e}")

@app.route('/article_recommendations', methods=['POST'])
def article_recommendations():
    
    try:
        # Parse user_id from request
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'status': 'error', 'message': 'User ID is required'}), 400
        
        # Load the chat memory for the user
        user_chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=3000,
            chat_store=chat_store,
            chat_store_key=f"user_{user_id}",
        )
        chat_history = user_chat_memory.chat_store.get_messages(user_chat_memory.chat_store_key)
        
        if not chat_history:
            return jsonify({'status': 'error', 'message': 'No queries found for this user'}), 404

        # Generate embeddings for all queries and calculate the average
        embeddings = []
        for query in chat_history:
            query_embedding = embedding_model.get_text_embedding(query.content)
            embeddings.append(query_embedding)

        # Calculate the average embedding
        average_embedding = [sum(x) / len(x) for x in zip(*embeddings)]
        
        
        vector_query = VectorStoreQuery(
            query_embedding=average_embedding,  # 嵌入向量
            similarity_top_k=10  # 返回前 10 个结果
        )
        
        # 调用查询
        search_results = vector_store.query(query=vector_query)
        articles = []
        
        for node in search_results.nodes:
            # 提取元数据
            content = node.get_content()
            print(f"Node content: {content}")
            article_id = node.metadata.get('article_id', 'Unknown')

            # 提取节点 ID 和嵌入向量
            node_id = node.id_
            
            # 构建结果
            articles.append({
                'id': node_id,
                'content': content,
                'article_id': article_id
            })
        
        response_data = {
            'status': 'success',
            'results': articles
            }
        response_data['history'] = [message.content for message in chat_history]
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route('/upload', methods=['POST'])
def upload_and_process():
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    try:
        # 上传文件到 genai
        myfile =genai.upload_file(filepath)
        print(f"{myfile=}")
        

        # 定义提示模板
        my_prompt = """
        Tell me the title, language, resource type, and content, publish time in this PDF. The language you need to determine by yourself.
        The publish time should be the input string to follow the ISO 8601 format.
        Return only valid JSON without any additional text, explanations, or formatting.
        Use this JSON schema:
        {"lang": str, "resource_type": str, "title": str, "publish_time": str, "content": str}
        Example response:
        {"lang": "English", "resource_type": "news", "title": "President Election 2024", "publish_time": "2024-10-25", "content": "xxx"}
        """

        # 调用模型生成内容
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content([my_prompt, myfile])
        

        try:
            # 打印原始输出
            print(f"Raw output: {repr(result.text)}")

            # 使用正则移除包裹符号
            clean_text = re.sub(r"^```json\n|```$", "", result.text.strip(), flags=re.MULTILINE)
            print(f"Cleaned output: {repr(clean_text)}")

            # 解析 JSON
            article_data = json.loads(clean_text)
            print(f"Parsed article data: {article_data}")

        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON. Error: {e}")
            print(f"Raw output: {repr(result.text)}")
            raise e
        # 数据库插入逻辑
        conn = create_connection()
        with conn.cursor() as cursor:
            
            requested_url = 'unknown'
            
            # 插入数据到 PostgreSQL
            insert_query = """
            INSERT INTO test_table (language, resource_type, title, publish_time, link, content)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            publish_time = datetime.fromisoformat(article_data.get('publish_time', datetime.now().isoformat()))
            cursor.execute(insert_query, (
                article_data.get('lang', 'English'),
                article_data.get('resource_type', 'news'),
                article_data['title'],
                publish_time,
                requested_url,
                article_data['content']
            ))
            article_id = cursor.fetchone()[0]

            # 处理内容分块
            content_string = article_data['content']
            content_bytes = content_string.encode('utf-8')
            byte_limit = 9800
            chunks = []
            current_index = 0

            while current_index < len(content_bytes):
                end_index = min(current_index + byte_limit, len(content_bytes))
                while end_index > current_index:
                    try:
                        chunk = content_bytes[current_index:end_index].decode('utf-8')
                        chunks.append(chunk)
                        current_index = end_index
                        break
                    except UnicodeDecodeError:
                        end_index -= 1
            
            #插入嵌入数据到 Pinecone
            for i, chunk in enumerate(chunks):
                embedding_result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=chunk,
                    task_type="retrieval_document",
                    title=article_data['title']
                )
                embedding = embedding_result['embedding']
                if requested_url=='unknown':
                    requested_url = f"article_{article_id}_{uuid.uuid4()}"
                index.upsert([
                    {
                        "id": f"{requested_url}_part_{i}",
                        "values": embedding,
                        "metadata": {
                            "key": 'content',
                            "content": chunk,
                            "article_id": article_id
                        }
                    }
                ])

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "data": {
                "article_id": article_id,
                "language": article_data['lang'],
                "resource_type": article_data.get('resource_type', 'news'),
                "title": article_data['title'],
                "publish_time": publish_time.isoformat(),
                "content": article_data['content']
            },
            "message": "Article processed successfully"
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        # 处理完成后删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
