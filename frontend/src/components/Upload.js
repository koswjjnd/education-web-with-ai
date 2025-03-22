import React, { useState } from 'react';

import { uploadFile } from '../services/api';

function FileUploadComponent() {
    const [file, setFile] = useState(null);
    const [message, setMessage] = useState('');
    const [isSuccess, setIsSuccess] = useState(null); // Tracks whether the upload succeeded or failed

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setMessage(''); // Clear any previous messages when a new file is selected
        setIsSuccess(null);
    };

    const handleUpload = async () => {
        if (!file) {
            setMessage('Please select a file to upload.');
            setIsSuccess(false); // Indicate failure
            return;
        }

        try {
            const response = await uploadFile(file);
            setMessage('File uploaded successfully!');
            setIsSuccess(true); // Indicate success
        } catch (error) {
            console.error('File upload failed:', error);
            setMessage('Failed to upload file. Please try again.');
            setIsSuccess(false); // Indicate failure
        }
    };

    return (
        <div style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
            <h1>Upload File</h1>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleUpload} style={{ marginTop: '10px' }}>
                Upload
            </button>
            {message && (
                <p
                    style={{
                        marginTop: '20px',
                        color: isSuccess ? 'green' : 'red', // Green for success, red for failure
                        fontWeight: 'bold',
                    }}
                >
                    {message}
                </p>
            )}
        </div>
    );
}

export default FileUploadComponent;
