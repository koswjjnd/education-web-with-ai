import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchArticleDetails } from '../services/api';

function ArticleDetails() {
    const { id } = useParams();
    const [article, setArticle] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getArticle = async () => {
            try {
                const response = await fetchArticleDetails(id);
                setArticle(response);
            } catch (err) {
                setError(err.message || 'Something went wrong');
            }
        };
        getArticle();
    }, [id]);

    if (error) {
        return <p style={{ color: 'red' }}>{error}</p>;
    }

    if (!article) {
        return <p>Loading...</p>;
    }

    return (
        <div>
            <h1>{article.title}</h1>
            <p><strong>Published:</strong> {article.publish_time}</p>
            <p><strong>Language:</strong> {article.language}</p>
            <p><strong>Resource Type:</strong> {article.resource_type}</p>
            <p>{article.content}</p>
        </div>
    );
}

export default ArticleDetails;
