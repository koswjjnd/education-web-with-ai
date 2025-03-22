from fundus import PublisherCollection, Crawler
from datetime import datetime
import pg8000
import google.generativeai as genai
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from dotenv import load_dotenv
import os
load_dotenv()
# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc=Pinecone(api_key=PINECONE_API_KEY)
index_name = "news-articles"
if not pc.has_index(index_name):
    pc.create_index(index_name, dimension=768, metric="cosine",
        spec=ServerlessSpec(
            cloud='aws', 
            region='us-east-1'
        ) )
index = pc.Index(index_name)

def insert_article_data(conn, article_data, article):
    with conn.cursor() as cursor:
        check_query = "SELECT COUNT(*) FROM test_table WHERE link = %s"
        cursor.execute(check_query, (article.html.requested_url,))
        result = cursor.fetchone()

        if result[0] > 0:
            print(f"Article already exists, skipping: {article_data['title']}")
            return

        insert_query = """
        INSERT INTO test_table (language, resource_type, title, publish_time, link, content)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """

        publish_time_str = article_data['publishing_date']
        publish_time = datetime.fromisoformat(publish_time_str) # Convert publish_time to a Python datetime object with timezone
        content = article_data['body']['sections'][0]['paragraphs']
        content_string = "\n".join(content) # convert it into string
        cursor.execute(insert_query, (
            article.lang,
            article_data.get('resource_type', 'news'),  # Assuming 'news' as default resource type
            article_data['title'],
            publish_time,
            article.html.requested_url,
            content_string
        ))
        #fetch the article_id
        article_id = cursor.fetchone()[0]

        byte_limit = 9800

        
        content_bytes = content_string.encode('utf-8')

       
        chunks = []
        current_index = 0

        while current_index < len(content_bytes):
            end_index = min(current_index + byte_limit, len(content_bytes))

            # 确保不会截断在多字节字符的中间，尝试解码
            while end_index > current_index:
                try:
                    chunk = content_bytes[current_index:end_index].decode('utf-8')
                    chunks.append(chunk)
                    current_index = end_index
                    break
                except UnicodeDecodeError:
                    # 如果解码失败，说明截断在多字节字符中间，需要调整 end_index
                    end_index -= 1

    
        for i, chunk in enumerate(chunks):
            
            embedding_result = genai.embed_content(
                model="models/text-embedding-004",
                content=chunk,
                task_type="retrieval_document",
                title=article_data['title']
            )
            embedding = embedding_result['embedding']

            
            index.upsert([
                {
                    "id": f"{article.html.requested_url}_part_{i}",
                    "values": embedding,
                    "metadata": {
                        "key": 'content',
                        "content": chunk,
                        "article_id": article_id
                    }
                }
            ])

    conn.commit()
def is_valid_content(article_data):
    """
    验证文章内容是否有效。
    :param article_data: 爬取的文章数据
    :return: True 表示内容有效，False 表示内容无效
    """
    # 检查标题是否存在且非空
    if not article_data.get('title') or len(article_data['title'].strip()) == 0:
        return False
    
    # 检查内容是否存在且非空
    content = article_data.get('body', {}).get('sections', [{}])[0].get('paragraphs', [])
    if not content:
        return False

    # 检查内容是否包含无效标志
    invalid_keywords = ["Explore other quiz", "Page not found", "404"]
    if any(keyword in " ".join(content) for keyword in invalid_keywords):
        return False

    return True

def check_db_connection(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT inet_server_addr(), inet_server_port();")
        server_info = cursor.fetchone()
        print(f"Connected to server IP: {server_info[0]}, Port: {server_info[1]}")

# Database connection setup
try:
    conn = pg8000.connect(
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT"))
    )

    # check_db_connection(conn)
    crawler = Crawler(PublisherCollection.us)
    # Crawl 2 articles
    for article in crawler.crawl(max_articles=1):
        # Get the article data as a dictionary
        article_data = article.to_json()
        if not is_valid_content(article_data):
            print(f"Skipping invalid article: {article_data.get('title', 'Unknown title')}")
            continue
        # Insert the article data into the database and Pinecone
        insert_article_data(conn, article_data, article)
        print(f"Inserted article: {article_data['title']}")
finally:
    # Close the database connection
    conn.close()
