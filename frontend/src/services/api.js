import config from '../config/config';
export const fetchRootContent = async () => {
    const response = await fetch(`${config.API_BASE_URL}/`, {
        method: 'GET',
    });

    if (!response.ok) {
        throw new Error('Failed to fetch root content');
    }

    return await response.json();
};
export const searchArticles = async (query, userId) => {
    const response = await fetch(`${config.API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, user_id: parseInt(userId) }),
    });

    if (!response.ok) {
        throw new Error('Failed to fetch search results');
    }

    return await response.json();
};
export const fetchUserSearchResults = async (userId) => {
    // Ensure the API_BASE_URL is set correctly
    const response = await fetch(`${config.API_BASE_URL}/article_recommendations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: parseInt(userId) }), // Pass the user ID
    });

    if (!response.ok) {
        throw new Error('Failed to fetch search results');
    }

    return await response.json();
};

export const fetchArticleDetails = async (articleId) => {
    const response = await fetch(`${config.API_BASE_URL}/article/${articleId}`, {
        method: 'GET',
    });

    if (!response.ok) {
        throw new Error('Failed to fetch article details');
    }

    const result = await response.json(); // 解析 JSON 响应
    return result.data; // 只返回 data 部分
};

export const uploadFile = async (file) => {
    const response = await fetch(`${config.API_BASE_URL}/upload`, {
        method: 'POST',
        body: (() => {
            const formData = new FormData();
            formData.append('file', file);
            return formData;
        })(),
    });

    if (!response.ok) {
        throw new Error('Failed to upload file');
    }

    return await response.json();
};
