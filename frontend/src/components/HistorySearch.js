import React, { useState, useEffect } from 'react';
import { fetchUserSearchResults } from '../services/api';
import { useNavigate, useSearchParams } from 'react-router-dom';

function HistorySearch() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    // 初始化搜索参数
    const initialUserId = searchParams.get('user_id') || '';

    // 状态管理
    const [userId, setUserId] = useState(initialUserId);
    const [articles, setArticles] = useState([]);
    const [history, setHistory] = useState([]);
    const [error, setError] = useState(null);

    // 初始化加载搜索结果（如果 URL 包含查询参数）
    useEffect(() => {
        if (initialUserId) {
            (async () => {
                try {
                    const response = await fetchUserSearchResults(initialUserId);
                    setArticles(response.results || []);
                    setHistory(response.history || []);
                } catch (err) {
                    setError(err.message || 'Failed to load search results');
                }
            })();
        }
    }, [initialUserId]);

    // 提交搜索
    const handleSearch = async (e) => {
        e.preventDefault();
        setError(null); // 清除之前的错误
        try {
            const response = await fetchUserSearchResults(userId);
            setArticles(response.results);
            setHistory(response.history);
            // 将搜索参数写入 URL
            navigate(`/article_recommendations?user_id=${userId}`);
        } catch (err) {
            setError(err.message || 'Failed to fetch search results');
        }
    };

    // 跳转到文章详情
    const handleArticleClick = (articleId) => {
        navigate(`/article/${articleId}`);
    };

    return (
        <div>
            <h1>History Search</h1>
            <form onSubmit={handleSearch}>
                <input
                    type="number"
                    placeholder="Enter your user ID"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    required
                />
                <button type="submit">Search</button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {/* 历史记录部分 */}
            {history.length > 0 && (
                <div>
                    <h2>Query History</h2>
                    <ul>
                        {history.map((query, index) => (
                            <li key={index}>{query}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* 文章列表部分 */}
            {articles.length > 0 && (
                <div>
                    <h2>Articles</h2>
                    <ul>
                        {articles.map((article) => (
                            <li key={article.id}>
                                <button onClick={() => handleArticleClick(article.article_id)}>
                                    View Article: {article.article_id || 'No Title'}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default HistorySearch;
