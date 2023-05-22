import React, { useState } from 'react';
import axios from 'axios';

function GenerateImage() {
  const [message, setMessage] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setImageUrl('');  // Clear the old image when a new prompt is submitted
    const response = await axios.post(
      process.env.REACT_APP_API_GATEWAY,  // replace with your API Gateway endpoint
      { message: message },
      { headers: { 'Content-Type': 'application/json' } }
    );

    // Parse the 'body' field from the API response
    let responseBody = JSON.parse(response.data.body);

    // Now you can access 'image_url' from the parsed body
    setImageUrl(responseBody.image_url);
  };

  const handleImageLoad = () => {
    setLoading(false);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          Prompt:
          <input type="text" value={message} onChange={e => setMessage(e.target.value)} />
        </label>
        <button type="submit">Generate Image</button>
      </form>
      {loading && <div className="loader"></div>}
      {imageUrl && (
        <div>
          <img src={imageUrl} alt="Generated" style={{ maxWidth: '100%' }} onLoad={handleImageLoad} />
        </div>
      )}
    </div>
  );
}

export default GenerateImage;
