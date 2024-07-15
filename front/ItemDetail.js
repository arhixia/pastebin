import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import './ItemDetail.css';

function ItemDetail() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchItem = async () => {
      const token = localStorage.getItem('token');
      try {
        const response = await fetch(`http://localhost:8000/items/${id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setItem(data);
        } else {
          console.error("Failed to fetch item details");
        }
      } catch (error) {
        console.error("An error occurred while fetching item details", error);
      }
    };
    fetchItem();
  }, [id]);

  if (!item) {
    return <div>Loading...</div>;
  }

  const url = window.location.href;

  return (
    <div className="item-detail-container">
      <h1>{item.title}</h1>
      <p>{item.content}</p>
      <small>Expires: {item.expiration_date ? new Date(item.expiration_date).toLocaleString() : 'Never'}</small>
      <p>Author: {item.owner_username}</p>
      <CopyToClipboard text={url} onCopy={() => setCopied(true)}>
        <button>Copy URL</button>
      </CopyToClipboard>
      {copied && <span style={{ color: 'green' }}>URL Copied!</span>}
    </div>
  );
}

export default ItemDetail;
