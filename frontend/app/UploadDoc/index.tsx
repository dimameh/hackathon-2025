import React, { useState } from 'react';
import axios from 'axios';

function UploadNote() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('note', file);
    try {
      
      const response = await axios.post("http://localhost:8080/api/upload", formData, {
        headers: { "Content-Type": "multipart/form-data", "Access-Control-Allow-Origin": "*" },
      });
      const data = response.data;
      setMessage(`Session ${data.session_id} created successfully.`);
    } catch (error) {
      console.error(error);
      setMessage('Error uploading file.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100vh', gap: '10px', paddingTop: '100px' }}>
      <h1 style={{ textAlign: 'center', fontWeight: 'bold' }}>Upload medical note</h1>
      <input type="file" onChange={handleFileChange} style={{ padding: '10px', borderRadius: '5px' }} />
      <button onClick={handleUpload} style={{ maxWidth: '200px', backgroundColor: 'blue', color: 'white', padding: '10px', borderRadius: '5px', border: '1px solid blue' }}>Upload</button>
      {message && <p style={{ textAlign: 'center' }}>{message}</p>}
    </div>
  );
}

export default UploadNote;