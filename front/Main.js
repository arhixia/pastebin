import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Main.css';

function Main({ username, setUsername, isModalOpen, setIsModalOpen }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [pastes, setPastes] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchPastes = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/items/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Ограничение контента до 10 слов
        const limitedData = data.map(item => ({
          ...item,
          content: item.content.split(' ').slice(0, 10).join(' ') + (item.content.split(' ').length > 10 ? '...' : '')
        }));
        setPastes(limitedData);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to fetch pastes!');
      }
    } catch (error) {
      setError('An error occurred. Please try again later.');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPastes();
  }, []);

  const handleCreatePaste = async (event) => {
    event.preventDefault();
    setLoading(true);

    const itemDetails = { title, content, expiration_date: expirationDate };

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/items/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(itemDetails),
      });

      if (response.ok) {
        fetchPastes();
        setTitle('');
        setContent('');
        setExpirationDate('');
        setIsModalOpen(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create paste!');
      }
    } catch (error) {
      setError('An error occurred. Please try again later.');
    }
    setLoading(false);
  };

  const openAddPasteModal = () => {
    setIsModalOpen(true);
  };

  const closeAddPasteModal = () => {
    setIsModalOpen(false);
  };

  return (
    <div className="main-container">
      {isModalOpen && (
        <div className="modal">
          <div className="modal-content">
            <span className="close-button" onClick={closeAddPasteModal}>&times;</span>
            <h2>Add Paste</h2>
            <form onSubmit={handleCreatePaste}>
              <label htmlFor="title">Title:</label><br />
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
              /><br />
              <label htmlFor="content">Content:</label><br />
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
                style={{ width: '100%', padding: '10px', marginBottom: '10px', minHeight: '100px' }}
              ></textarea><br />
              <label htmlFor="expirationDate">Expiration Date:</label><br />
              <input
                type="datetime-local"
                id="expirationDate"
                value={expirationDate}
                onChange={(e) => setExpirationDate(e.target.value)}
                style={{ width: '100%', padding: '10px', marginBottom: '20px' }}
              /><br />
              <button type="submit" className="add-paste-button" disabled={loading}>
                {loading ? 'Creating...' : 'Create'}
              </button>
            </form>
            {error && <p className="error">{error}</p>}
          </div>
        </div>
      )}
      <div className="pastes-container">
        {pastes.map((paste) => (
          <div key={paste.id} className="paste-item">
            <h3>{paste.title}</h3>
            <p>{paste.content}</p>
            <small>Expires: {paste.expiration_date ? new Date(paste.expiration_date).toLocaleString() : 'Never'}</small>
            <p>Author: {paste.owner_username}</p>
            <Link to={`/${paste.id}`} className="view-details-link">View Details</Link>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Main;