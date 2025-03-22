import React, { useState, useEffect } from 'react';
import { searchArticles } from '../services/api';
import { useNavigate, useSearchParams } from 'react-router-dom';

function Search() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    // 初始化搜索参数
    const initialQuery = searchParams.get('query') || '';
    const initialUserId = searchParams.get('user_id') || '';

    // 状态管理
    const [query, setQuery] = useState(initialQuery);
    const [userId, setUserId] = useState(initialUserId);
    const [articles, setArticles] = useState([]);
    const [summary, setSummary] = useState('');
    const [error, setError] = useState(null);
    const [mostRecommendedId, setMostRecommendedId] = useState(null);

    // 初始化加载搜索结果（如果 URL 包含查询参数）
    useEffect(() => {
        if (initialQuery && initialUserId) {
            (async () => {
                try {
                    const response = await searchArticles(initialQuery, initialUserId);
                    setSummary(response.summary);
                    setArticles(response.data);
                    if (response.most_recommended) {
                        setMostRecommendedId(response.most_recommended.article_id);
                    } else {
                        setMostRecommendedId(null);
                    }
                } catch (err) {
                    setError(err.message || 'Failed to load search results');
                }
            })();
        }
    }, [initialQuery, initialUserId]);

    // 提交搜索
    const handleSearch = async (e) => {
        e.preventDefault();
        setError(null); // 清除之前的错误
        try {
            const response = await searchArticles(query, userId);
            setSummary(response.summary);
            setArticles(response.data);
            if (response.most_recommended) {
                setMostRecommendedId(response.most_recommended.article_id);
            } else {
                setMostRecommendedId(null);
            }
            // 将搜索参数写入 URL
            navigate(`/search?query=${encodeURIComponent(query)}&user_id=${userId}`);
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
            <h1>Search Articles</h1>
            <form onSubmit={handleSearch}>
                <input
                    type="text"
                    placeholder="Enter your query"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    required
                />
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
            {summary && (
                <div>
                    <h2>Summary</h2>
                    <p>{summary}</p>
                </div>
            )}
            {articles.length > 0 && (
                <ul>
                    {articles.map((id) => (
                        <li key={id}>
                            <button onClick={() => handleArticleClick(id)}>
                                {id === mostRecommendedId ? 'Most Recommended: ' : ''}
                                View Article {id}
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default Search;