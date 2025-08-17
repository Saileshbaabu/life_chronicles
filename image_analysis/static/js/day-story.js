// Day Story Creator Functions - Complete Rewrite

// Global variables
let availablePhotos = [];
let selectedPhotos = [];
let uploadedPhotos = [];

// Initialize Day Story Creator
function initializeDayStoryCreator() {
    console.log('Initializing Day Story Creator...');
    
    // Reset state
    availablePhotos = [];
    selectedPhotos = [];
    
    // Load photos
    loadAvailablePhotos();
    
    // Initialize event listeners
    initializeEventListeners();
    
    console.log('Day Story Creator initialized successfully');
}

// Initialize event listeners
function initializeEventListeners() {
    // Create story button
    const createBtn = document.getElementById('createStoryBtn');
    if (createBtn) {
        createBtn.addEventListener('click', createDayStory);
    }
    
    // Language selector
    const langSelector = document.getElementById('storyLanguage');
    if (langSelector) {
        langSelector.addEventListener('change', updateStoryOptions);
    }
    
    // Tone selector
    const toneSelector = document.getElementById('storyTone');
    if (toneSelector) {
        toneSelector.addEventListener('change', updateStoryOptions);
    }
    
    // Length selector
    const lengthSelector = document.getElementById('storyLength');
    if (lengthSelector) {
        lengthSelector.addEventListener('change', updateStoryOptions);
    }
}

// Load available photos
function loadAvailablePhotos() {
    console.log('Loading available photos...');
    
    // Use uploaded photos if available, otherwise fall back to mock data
    if (uploadedPhotos && uploadedPhotos.length > 0) {
        console.log('Using uploaded photos:', uploadedPhotos.length);
        availablePhotos = uploadedPhotos.map((photo, index) => ({
            id: `uploaded_${index}`,
            filename: photo.filename || `photo_${index + 1}.jpg`,
            date: photo.date || new Date().toISOString().split('T')[0],
            time: photo.time || '12:00',
            daypart: photo.daypart || 'afternoon',
            imageData: photo.imageData,
            analysis: photo.analysis
        }));
    } else {
        console.log('No uploaded photos, using mock data');
        // Mock data for demonstration
        availablePhotos = [
            {
                id: '1',
                filename: 'morning_photo.jpg',
                date: '2024-01-15',
                time: '07:30',
                daypart: 'morning'
            },
            {
                id: '2',
                filename: 'afternoon_photo.jpg',
                date: '2024-01-15',
                time: '14:15',
                daypart: 'afternoon'
            },
            {
                id: '3',
                filename: 'evening_photo.jpg',
                date: '2024-01-15',
                time: '18:45',
                daypart: 'evening'
            }
        ];
    }
    
    console.log('Available photos loaded:', availablePhotos.length);
    console.log('Available photos data:', availablePhotos);
    
    // Update the uploaded photo count display
    updateUploadedPhotoCount();
    
    // Render the photo grid
    renderPhotoGrid();
}

// Update uploaded photo count
function updateUploadedPhotoCount() {
    const uploadedPhotoCount = document.getElementById('uploadedPhotoCount');
    if (uploadedPhotoCount) {
        uploadedPhotoCount.textContent = uploadedPhotos.length;
        console.log('Updated uploaded photo count to:', uploadedPhotos.length);
    } else {
        console.warn('uploadedPhotoCount element not found');
    }
}

// Render photo grid
function renderPhotoGrid() {
    console.log('Rendering photo grid...');
    
    const photoGrid = document.getElementById('photoGrid');
    if (!photoGrid) {
        console.error('Photo grid element not found!');
        return;
    }
    
    // Clear the grid completely
    photoGrid.innerHTML = '';
    console.log('Photo grid cleared');
    
    if (availablePhotos.length === 0) {
        console.log('No photos available, showing empty state');
        photoGrid.innerHTML = `
            <div style="text-align: center; color: #666; padding: 40px; grid-column: 1 / -1;">
                <i class="fas fa-images" style="font-size: 2rem; margin-bottom: 10px; display: block;"></i>
                <p>No photos available</p>
                <p style="font-size: 12px; margin-top: 10px;">Upload some photos to get started!</p>
            </div>
        `;
        return;
    }
    
    console.log('Rendering', availablePhotos.length, 'photos');
    
    // Create photo items
    availablePhotos.forEach((photo, index) => {
        console.log(`Creating photo item ${index + 1}/${availablePhotos.length} for:`, photo.filename);
        
        const photoItem = createPhotoItem(photo);
        photoGrid.appendChild(photoItem);
        
        console.log('Photo item added to grid:', photoItem);
    });
    
    console.log('Final photo grid HTML:', photoGrid.innerHTML);
    console.log('Photo grid children count:', photoGrid.children.length);
    
    // Update selected count
    updateSelectedCount();
    
    console.log('Photo grid rendered successfully');
}

// Create individual photo item
function createPhotoItem(photo) {
    const photoItem = document.createElement('div');
    photoItem.className = `photo-item ${selectedPhotos.includes(photo.id) ? 'selected' : ''}`;
    photoItem.onclick = () => togglePhotoSelection(photo.id);
    
    const daypartColor = getDaypartColor(photo.daypart);
    console.log('Daypart color for', photo.daypart, ':', daypartColor);
    
    // Create photo content
    if (photo.imageData) {
        console.log('Rendering photo with image data:', photo.filename);
        photoItem.innerHTML = createImagePhotoHTML(photo, daypartColor);
    } else {
        console.log('Rendering photo with placeholder:', photo.filename);
        photoItem.innerHTML = createPlaceholderPhotoHTML(photo, daypartColor);
    }
    
    return photoItem;
}

// Create HTML for photo with actual image
function createImagePhotoHTML(photo, daypartColor) {
    return `
        <div class="photo-image-container">
            <img src="${photo.imageData}" alt="${photo.filename}" 
                 class="photo-image" 
                 onload="console.log('Image loaded successfully:', '${photo.filename}')" 
                 onerror="console.error('Image failed to load:', '${photo.filename}')">
        </div>
        <div class="photo-info">
            <div class="photo-filename">${photo.filename}</div>
            <div class="photo-time">${photo.time}</div>
            <div class="daypart-badge" style="background-color: ${daypartColor}">
                ${photo.daypart}
            </div>
        </div>
    `;
}

// Create HTML for photo placeholder
function createPlaceholderPhotoHTML(photo, daypartColor) {
    return `
        <div class="photo-placeholder" style="background-color: ${daypartColor};">
            <div class="placeholder-icon">
                <i class="fas fa-image"></i>
            </div>
            <div class="placeholder-text">${photo.daypart.toUpperCase()}</div>
        </div>
        <div class="photo-info">
            <div class="photo-filename">${photo.filename}</div>
            <div class="photo-time">${photo.time}</div>
            <div class="daypart-badge" style="background-color: ${daypartColor}">
                ${photo.daypart}
            </div>
        </div>
    `;
}

// Toggle photo selection
function togglePhotoSelection(photoId) {
    console.log('Toggling photo selection:', photoId);
    
    if (selectedPhotos.includes(photoId)) {
        selectedPhotos = selectedPhotos.filter(id => id !== photoId);
        console.log('Photo deselected:', photoId);
    } else {
        selectedPhotos.push(photoId);
        console.log('Photo selected:', photoId);
    }
    
    // Re-render to update selection styling
    renderPhotoGrid();
    
    // Update selected count
    updateSelectedCount();
}

// Update selected count display
function updateSelectedCount() {
    const selectedCount = document.getElementById('selectedCount');
    if (selectedCount) {
        selectedCount.textContent = selectedPhotos.length;
        console.log('Updated selected count to:', selectedPhotos.length);
    } else {
        console.warn('selectedCount element not found');
    }
}

// Update story options based on selections
function updateStoryOptions() {
    const lang = document.getElementById('storyLanguage')?.value || 'en';
    const tone = document.getElementById('storyTone')?.value || 'diary';
    const length = document.getElementById('storyLength')?.value || 'medium';
    
    console.log('Story options updated:', { lang, tone, length });
    
    // Update create button state
    const createBtn = document.getElementById('createStoryBtn');
    if (createBtn) {
        createBtn.disabled = selectedPhotos.length === 0;
        if (selectedPhotos.length === 0) {
            createBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Select Photos First';
        } else {
            createBtn.innerHTML = '<i class="fas fa-magic"></i> Create Day Story';
        }
    }
}

// Create day story
function createDayStory() {
    console.log('Creating day story...');
    
    if (selectedPhotos.length === 0) {
        showError('Please select at least one photo');
        return;
    }
    
    const lang = document.getElementById('storyLanguage')?.value || 'en';
    const tone = document.getElementById('storyTone')?.value || 'diary';
    const length = document.getElementById('storyLength')?.value || 'medium';
    
    console.log('Story parameters:', { lang, tone, length, selectedPhotos });
    
    // Show loading state
    const createBtn = document.getElementById('createStoryBtn');
    const originalText = createBtn.innerHTML;
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Story...';
    }
    
    // Mock API call - in real app, this would call the actual stories API
    setTimeout(() => {
        try {
            // Generate mock story based on selected options
            const story = generateMockStory(selectedPhotos, lang, tone, length);
            displayGeneratedStory(story);
            
            console.log('Story created successfully:', story);
        } catch (error) {
            console.error('Error creating story:', error);
            showError('Failed to create story. Please try again.');
        } finally {
            // Reset button
            if (createBtn) {
                createBtn.disabled = false;
                createBtn.innerHTML = originalText;
            }
        }
    }, 2000);
}

// Generate mock story
function generateMockStory(photoIds, lang, tone, length) {
    console.log('Generating mock story for:', { photoIds, lang, tone, length });
    
    const photos = availablePhotos.filter(p => photoIds.includes(p.id));
    const dayparts = [...new Set(photos.map(p => p.daypart))].sort();
    
    console.log('Photos for story:', photos);
    console.log('Dayparts:', dayparts);
    
    // Generate story based on language
    if (lang === 'ta') {
        return {
            title: getTamilTitle(tone, dayparts),
            subtitle: getTamilSubtitle(tone, photos.length),
            intro_md: getTamilIntro(tone, dayparts),
            sections: photos.map((photo, index) => ({
                media_id: photo.id,
                section_heading: getTamilDaypart(photo.daypart),
                section_content: getTamilSectionContent(photo, tone, length)
            }))
        };
    } else {
        return {
            title: getEnglishTitle(tone, dayparts),
            subtitle: getEnglishSubtitle(tone, photos.length),
            intro_md: getEnglishIntro(tone, dayparts),
            sections: photos.map((photo, index) => ({
                media_id: photo.id,
                section_heading: getEnglishDaypart(photo.daypart),
                section_content: getEnglishSectionContent(photo, tone, length)
            }))
        };
    }
}

// Display generated story
function displayGeneratedStory(story) {
    console.log('Displaying generated story:', story);
    
    const generatedStory = document.getElementById('generatedStory');
    const storyContent = document.getElementById('storyContent');
    
    if (!generatedStory || !storyContent) {
        console.error('Story display elements not found');
        return;
    }
    
    // Create story HTML
    let storyHTML = `
        <div class="story-header">
            <h2 class="story-title">${story.title}</h2>
            <p class="story-subtitle">${story.subtitle}</p>
        </div>
        <div class="story-intro">
            ${story.intro_md}
        </div>
        <div class="story-sections">
    `;
    
    story.sections.forEach((section, index) => {
        storyHTML += `
            <div class="story-section">
                <h3 class="section-heading">${section.section_heading}</h3>
                <div class="section-content">
                    ${section.section_content}
                </div>
            </div>
        `;
    });
    
    storyHTML += `
        </div>
        <div class="story-actions">
            <button class="btn btn-primary" onclick="downloadStory()">
                <i class="fas fa-download"></i> Download Story
            </button>
            <button class="btn btn-secondary" onclick="shareStory()">
                <i class="fas fa-share"></i> Share Story
            </button>
        </div>
    `;
    
    storyContent.innerHTML = storyHTML;
    generatedStory.style.display = 'block';
    
    // Scroll to story
    generatedStory.scrollIntoView({ behavior: 'smooth' });
    
    console.log('Story displayed successfully');
}

// Helper functions for story generation
function getEnglishTitle(tone, dayparts) {
    const toneMap = {
        diary: 'A Day in My Life',
        travelogue: 'My Journey Through the Day',
        reportage: 'Daily Chronicle Report'
    };
    return toneMap[tone] || 'My Day Story';
}

function getEnglishSubtitle(tone, photoCount) {
    return `Capturing ${photoCount} moments across ${dayparts.length} time periods`;
}

function getEnglishIntro(tone, dayparts) {
    return `This story captures the essence of a day through ${dayparts.join(', ')} moments, each telling its own unique tale.`;
}

function getEnglishDaypart(daypart) {
    const daypartMap = {
        morning: 'Morning',
        afternoon: 'Afternoon',
        evening: 'Evening',
        night: 'Night'
    };
    return daypartMap[daypart] || daypart;
}

function getEnglishSectionContent(photo, tone, length) {
    const baseContent = `This ${photo.daypart} moment captures ${photo.filename} at ${photo.time}.`;
    
    if (length === 'short') {
        return baseContent;
    } else if (length === 'medium') {
        return `${baseContent} The ${photo.daypart} light brings out the unique character of this scene.`;
    } else {
        return `${baseContent} The ${photo.daypart} light brings out the unique character of this scene. This moment represents the transition and mood of the ${photo.daypart} period.`;
    }
}

// Tamil helper functions
function getTamilTitle(tone, dayparts) {
    const toneMap = {
        diary: 'என் வாழ்க்கையில் ஒரு நாள்',
        travelogue: 'நாள் முழுவதும் என் பயணம்',
        reportage: 'தினசரி நிகழ்வு அறிக்கை'
    };
    return toneMap[tone] || 'என் நாள் கதை';
}

function getTamilSubtitle(tone, photoCount) {
    return `${photoCount} கணங்களை ${dayparts.length} நேரப்பிரிவுகளில் பிடித்தது`;
}

function getTamilIntro(tone, dayparts) {
    return `இந்த கதை ${dayparts.join(', ')} கணங்களில் ஒரு நாளின் சாரத்தை பிடிக்கிறது, ஒவ்வொன்றும் தனக்கென தனித்த கதையை சொல்கிறது.`;
}

function getTamilDaypart(daypart) {
    const daypartMap = {
        morning: 'காலை',
        afternoon: 'மதியம்',
        evening: 'மாலை',
        night: 'இரவு'
    };
    return daypartMap[daypart] || daypart;
}

function getTamilSectionContent(photo, tone, length) {
    const baseContent = `இந்த ${getTamilDaypart(photo.daypart)} கணம் ${photo.filename} ஐ ${photo.time} மணிக்கு பிடிக்கிறது.`;
    
    if (length === 'short') {
        return baseContent;
    } else if (length === 'medium') {
        return `${baseContent} ${getTamilDaypart(photo.daypart)} ஒளி இந்த காட்சியின் தனித்துவமான பண்பை வெளிக்கொணர்கிறது.`;
    } else {
        return `${baseContent} ${getTamilDaypart(photo.daypart)} ஒளி இந்த காட்சியின் தனித்துவமான பண்பை வெளிக்கொணர்கிறது. இந்த கணம் ${getTamilDaypart(photo.daypart)} காலத்தின் மாற்றத்தையும் மனநிலையையும் குறிக்கிறது.`;
    }
}

// Utility functions
function getDaypartColor(daypart) {
    const colors = {
        morning: '#4CAF50',    // Green
        afternoon: '#FF9800',  // Orange
        evening: '#9C27B0',    // Purple
        night: '#2196F3'       // Blue
    };
    return colors[daypart] || '#666';
}

// Error handling
function showError(message) {
    console.error('Error:', message);
    
    // Create or update error message element
    let errorElement = document.getElementById('dayStoryError');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = 'dayStoryError';
        errorElement.className = 'error-message';
        errorElement.style.cssText = `
            background-color: #ffebee;
            color: #c62828;
            padding: 12px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #ffcdd2;
            text-align: center;
        `;
        
        // Insert after photo grid
        const photoGrid = document.getElementById('photoGrid');
        if (photoGrid && photoGrid.parentNode) {
            photoGrid.parentNode.insertBefore(errorElement, photoGrid.nextSibling);
        }
    }
    
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

// Download story function
function downloadStory() {
    console.log('Downloading story...');
    // Implementation for downloading story
    alert('Download functionality coming soon!');
}

// Share story function
function shareStory() {
    console.log('Sharing story...');
    // Implementation for sharing story
    alert('Share functionality coming soon!');
}

// Export functions for global access
window.initializeDayStoryCreator = initializeDayStoryCreator;
window.loadAvailablePhotos = loadAvailablePhotos;
window.renderPhotoGrid = renderPhotoGrid;
window.togglePhotoSelection = togglePhotoSelection;
window.createDayStory = createDayStory;
window.updateStoryOptions = updateStoryOptions;
