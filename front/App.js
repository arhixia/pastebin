// App.js

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './Header';
import Main from './Main';
import Login from './Login';
import Register from './Register';
import ItemDetail from './ItemDetail';
import './App.css';

function App() {
  const [username, setUsername] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUsername('');
    window.location.href = '/'; // Redirect to the root URL after logout
  };

  return (
    <Router>
      <div className="app-container">
        <Header
          username={username}
          handleLogout={handleLogout}
          setIsModalOpen={setIsModalOpen}
        />
        <Routes>
          <Route path="/" element={<Main username={username} setUsername={setUsername} isModalOpen={isModalOpen} setIsModalOpen={setIsModalOpen} />} />
          <Route path="/login" element={<Login setUsername={setUsername} />} />
          <Route path="/register" element={<Register />} />
          <Route path="/:id" element={<ItemDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
