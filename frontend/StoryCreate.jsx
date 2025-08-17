import React, { useState, useEffect } from 'react';
import './StoryCreate.css';

const StoryCreate = () => {
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [availablePhotos, setAvailablePhotos] = useState([]);
  const [storyOptions, setStoryOptions] = useState({
    lang: 'en',
    tone: 'diary',
    length: 'medium'
  });
  const [loading, setLoading] = useState(false);
  const [generatedStory, setGeneratedStory] = useState(null);
  const [error, setError] = useState(null);

  // Mock data for available photos (in real app, this would come from API)
  useEffect(() => {
    // Simulate fetching available photos
    const mockPhotos = [
      {
        id: '1',
        filename: 'morning_photo.jpg',
        date: '2024-01-15',
        time: '07:30',
        daypart: 'morning',
        thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y0ZjRmNCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+TW9ybmluZzwvdGV4dD48L3N2Zz4='
      },
      {
        id: '2',
        filename: 'afternoon_photo.jpg',
        date: '2024-01-15',
        time: '14:15',
        daypart: 'afternoon',
        thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2ZmYzEwNyIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+QWZ0ZXJub29uPC90ZXh0Pjwvc3ZnPg=='
      },
      {
        id: '3',
        filename: 'evening_photo.jpg',
        date: '2024-01-15',
        time: '18:45',
        daypart: 'evening',
        thumbnail: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2ZmOTgwMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+RXZlbmluZzwvdGV4dD48L3N2Zz4='
      }
    ];
    setAvailablePhotos(mockPhotos);
  }, []);

  const handlePhotoToggle = (photoId) => {
    setSelectedPhotos(prev => {
      if (prev.includes(photoId)) {
        return prev.filter(id => id !== photoId);
      } else {
        return [...prev, photoId];
      }
    });
  };

  const handleOptionChange = (option, value) => {
    setStoryOptions(prev => ({
      ...prev,
      [option]: value
    }));
  };

  const handleCreateStory = async () => {
    if (selectedPhotos.length === 0) {
      setError('Please select at least one photo');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Mock API call - replace with actual API endpoint
      const response = await fetch('/api/stories/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-token' // Replace with actual auth
        },
        body: JSON.stringify({
          media_ids: selectedPhotos,
          ...storyOptions
        })
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedStory(data.story_json);
      } else {
        throw new Error('Failed to create story');
      }
    } catch (err) {
      setError(err.message);
      // For demo purposes, show mock story
      setGeneratedStory({
        title: "A Day's Journey",
        subtitle: "Memories captured in photographs",
        intro_md: "Today we traveled to many places. Each photograph tells a story.",
        sections: [
          {
            media_id: "1",
            section_heading: "Morning Time",
            body_md: "At 7:30 AM we left home to begin our journey.",
            image_caption: "House in morning sunlight",
            alt_text: "Photograph of house taken in the morning",
            tags: ["morning", "house", "sunlight"]
          },
          {
            media_id: "2",
            section_heading: "Afternoon Adventure",
            body_md: "By 2:15 PM we had reached our destination.",
            image_caption: "Scenic afternoon view",
            alt_text: "Beautiful landscape captured in afternoon light",
            tags: ["afternoon", "landscape", "adventure"]
          },
          {
            media_id: "3",
            section_heading: "Evening Return",
            body_md: "As the sun set at 6:45 PM, we headed back home.",
            image_caption: "Sunset over the horizon",
            alt_text: "Stunning sunset view as we concluded our day",
            tags: ["evening", "sunset", "return"]
          }
        ],
        outro_md: "What we experienced throughout this day is unforgettable."
      });
    } finally {
      setLoading(false);
    }
  };

  const getDaypartColor = (daypart) => {
    const colors = {
      morning: '#4CAF50',
      afternoon: '#FF9800',
      evening: '#9C27B0',
      night: '#2196F3'
    };
    return colors[daypart] || '#666';
  };

  return (
    <div className="story-create">
      <h1>Create Your Day Story</h1>
      
      {/* Photo Selection */}
      <div className="photo-selection">
        <h2>Select Photos</h2>
        <div className="photo-grid">
          {availablePhotos.map(photo => (
            <div 
              key={photo.id} 
              className={`photo-item ${selectedPhotos.includes(photo.id) ? 'selected' : ''}`}
              onClick={() => handlePhotoToggle(photo.id)}
            >
              <img src={photo.thumbnail} alt={photo.filename} />
              <div className="photo-info">
                <div className="photo-filename">{photo.filename}</div>
                <div className="photo-time">{photo.time}</div>
                <div 
                  className="daypart-badge"
                  style={{ backgroundColor: getDaypartColor(photo.daypart) }}
                >
                  {photo.daypart}
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="selection-info">
          Selected: {selectedPhotos.length} photo{selectedPhotos.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Story Options */}
      <div className="story-options">
        <h2>Story Options</h2>
        <div className="options-grid">
          <div className="option-group">
            <label>Language:</label>
            <select 
              value={storyOptions.lang} 
              onChange={(e) => handleOptionChange('lang', e.target.value)}
            >
              <option value="en">English</option>
              <option value="ta">Tamil</option>
            </select>
          </div>

          <div className="option-group">
            <label>Tone:</label>
            <select 
              value={storyOptions.tone} 
              onChange={(e) => handleOptionChange('tone', e.target.value)}
            >
              <option value="diary">Diary</option>
              <option value="travelogue">Travelogue</option>
              <option value="reportage">Reportage</option>
            </select>
          </div>

          <div className="option-group">
            <label>Length:</label>
            <select 
              value={storyOptions.length} 
              onChange={(e) => handleOptionChange('length', e.target.value)}
            >
              <option value="short">Short</option>
              <option value="medium">Medium</option>
              <option value="long">Long</option>
            </select>
          </div>
        </div>
      </div>

      {/* Create Button */}
      <div className="create-section">
        <button 
          className="create-button"
          onClick={handleCreateStory}
          disabled={loading || selectedPhotos.length === 0}
        >
          {loading ? 'Creating Story...' : 'Create Day Story'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Generated Story Display */}
      {generatedStory && (
        <div className="generated-story">
          <h2>Your Generated Story</h2>
          <div className="story-content">
            <h1 className="story-title">{generatedStory.title}</h1>
            <h2 className="story-subtitle">{generatedStory.subtitle}</h2>
            
            <div className="story-intro">
              {generatedStory.intro_md}
            </div>

            <div className="story-sections">
              {generatedStory.sections.map((section, index) => (
                <div key={index} className="story-section">
                  <h3 className="section-heading">{section.section_heading}</h3>
                  <p className="section-body">{section.body_md}</p>
                  <div className="section-meta">
                    <p className="image-caption">{section.image_caption}</p>
                    <div className="tags">
                      {section.tags.map((tag, tagIndex) => (
                        <span key={tagIndex} className="tag">{tag}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="story-outro">
              {generatedStory.outro_md}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryCreate;
