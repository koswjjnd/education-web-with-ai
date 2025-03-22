import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchRootContent } from './services/api';

function Home() {
    const [message, setMessage] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchRootContent();
                setMessage(data.message);
            } catch (err) {
                setError('Failed to load content.');
                console.error(err);
            }
        };

        fetchData();
    }, []);

    return (
        <div>
            <h1>Home Page</h1>
            {error ? <p>{error}</p> : <p>{message}</p>}
            <Link to="/search">Go to Search</Link>
            <Link to="/upload">Go to Upload</Link>
            <Link to="/article_recommendations">Go to User History Queries Search </Link>
        </div>
    );
}

export default Home;
