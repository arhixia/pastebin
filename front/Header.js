import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

function Header({ username, handleLogout, setIsModalOpen }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <h1>Pastebin</h1>
      </div>
      <div className="header-right">
        {username ? (
          <>
            <button className="add-paste-button" onClick={() => setIsModalOpen(true)}>Add Paste</button>
            <span className="username">{username}</span>
            <button className="logout-button" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/register" className="header-link">Sign up</Link>
            <Link to="/login" className="header-link">Login</Link>
          </>
        )}
      </div>
    </header>
  );
}

export default Header;

