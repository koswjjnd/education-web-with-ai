import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Home';
import Search from './components/Search';
import ArticleDetails from './components/ArticleDetails';
import FileUploadComponent from './components/Upload';
import HistorySearch from './components/HistorySearch';
function App() {
    return (
        <Router>
            <div>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/search" element={<Search />} />
                    <Route path="/article/:id" element={<ArticleDetails />} />
                    <Route path="/upload" element={<FileUploadComponent />} /> 
                    <Route path="/article_recommendations" element={<HistorySearch />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;


