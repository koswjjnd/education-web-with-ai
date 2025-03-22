# 📚 Educational Web Application

## 📌 Introduction
This is an **educational web application** that consists of a **frontend** for UI display and a **backend** providing multiple functionalities, including **CRUD operations, AI-powered article analysis, chatbot-based search, and personalized recommendations**.

### 🔹 Backend Features
- **CRUD API**: Supports creating, reading, updating, and deleting articles.
- **GenAI Integration**: When a new article is created, the backend calls GenAI to **analyze and summarize** the uploaded article’s title and content.  (app.py)
- **Chatbot Interaction – Search API**: Uses **LlamaIndex** to query **Pinecone** based on user inquiries, retrieving and recommending relevant articles.  (app.py)
- **Article Recommendations API**: Suggests articles based on a user's **past search history, learning language, and proficiency level**. (app.py)
- **Web Crawling**: Automatically extracts article content from the web and stores it in **PostgreSQL** (for structured storage) and **Pinecone** (for vector search), implemented in AWS Lambda. (book.py)
- **Test API**: Implemented unit tests for three key APIs—article_recommendations, search_articles, and upload_article—verifying both successful and failure cases to ensure they behave as expected. (test_app.py)

## 📌 Running Locally  

### 🛠 Backend
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Navigate back to the root directory and Start the application with docker compose
   ```bash
   cd ..
   docker-compose up --build
   ```

Alternative method without Docker Compose (without setting up databases):
3. Build the Docker image:
   ```bash
   docker build -t simple-server .
   ```
4. Run the container:
   ```bash
   docker run -p 5000:5000 simple-server
   ```
}

### 💻 Frontend
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Start the development server:
   ```bash
   npm install
   ```
   ```bash
   npm start
   ```
### 🛠 Test App
1. After start the backend by using Docker, navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Find the running container's ID:
   ```bash
   docker ps
   ```
3. Run tests inside the container:
   ```bash
   docker exec -it <CONTAINER_ID> pytest test_app.py
   ```

## 🚀 Deploying on AWS  

### 🛠 Backend Deployment (AWS ECS)
1. **Upload Docker image to AWS ECR**:
   - Build and push the image to **AWS Elastic Container Registry (ECR)**.
2. **Create an ECS Cluster**:
   - Set up **Amazon ECS** to manage containerized applications.
3. **Deploy the ECR image to the ECS cluster**:
   - ECS retrieves the stored image from **ECR** and runs it as a fully processed containerized service.
   - **ECS depends on ECR** to store and manage container images.

### 🎨 Frontend Deployment (AWS S3)
The frontend follows a typical **React deployment process**, involving:
1. **Transpilation** → Converting JSX/ES6 code into browser-compatible JavaScript.
2. **Bundling** → Optimizing and packaging JavaScript files.
3. **Static File Generation** → Producing optimized assets for deployment.
4. **AWS S3 Hosting** → Uploading the generated static files to an **S3 bucket** for scalable hosting.

## 🔧 Technologies Used
- **Frontend**: React, JavaScript, HTML, CSS
- **Backend**: Flask, PostgreSQL, Pinecone, LlamaIndex, GenAI
- **Deployment**: Docker, AWS ECS, AWS S3, AWS ECR, AWS Lambda

---
