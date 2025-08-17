// Image Analysis Functions

function uploadImage(file) {
    // Show image preview first
    showImagePreview(file);
    
    // Store the image data for Day Story Creator
    const reader = new FileReader();
    reader.onload = function(e) {
        // Store the image data globally for later use
        window.currentUploadedImageData = e.target.result;
    };
    reader.readAsDataURL(file);
    
    const formData = new FormData();
    formData.append('image', file);
    
    // Add language selection
    const selectedLanguage = document.getElementById('languageSelect').value;
    formData.append('target_language', selectedLanguage);

    // Show loading state
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('resultsSection');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if (loading) loading.style.display = 'block';
    if (resultsSection) resultsSection.style.display = 'none';
    if (errorMessage) errorMessage.style.display = 'none';
    if (successMessage) successMessage.style.display = 'none';
    if (uploadBtn) uploadBtn.disabled = true;
    
    // Clear previous analysis results but keep image preview
    const imageAnalysis = document.getElementById('imageAnalysis');
    const articleContent = document.getElementById('articleContent');
    const metadataGrid = document.getElementById('metadataGrid');
    
    if (imageAnalysis) imageAnalysis.innerHTML = '';
    if (articleContent) articleContent.innerHTML = '';
    if (metadataGrid) metadataGrid.innerHTML = '';

    fetch('/api/analyze-image/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // Check if response is ok
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Check if response has content
        const contentType = response.headers.get('content-type');
        console.log('Response content type:', contentType);
        console.log('Response status:', response.status);
        
        if (!contentType || !contentType.includes('application/json')) {
            console.warn('Response content type is not JSON:', contentType);
        }
        
        // Try to parse JSON with better error handling
        return response.text().then(text => {
            console.log('Raw response text:', text.substring(0, 200) + '...');
            
            if (!text || text.trim() === '') {
                throw new Error('Empty response from server');
            }
            
            try {
                return JSON.parse(text);
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                console.error('Response text that failed to parse:', text);
                throw new Error(`Failed to parse JSON response: ${parseError.message}`);
            }
        });
    })
    .then(data => {
        if (loading) loading.style.display = 'none';
        if (uploadBtn) uploadBtn.disabled = false;

        // Debug: Log the received data
        console.log('Received API response:', data);
        console.log('Article data:', data.article);

        if (data.error) {
            showError(data.error + (data.details ? ': ' + JSON.stringify(data.details) : ''));
        } else {
            showResults(data);
            showSuccess('Image analyzed successfully!');
            // Show results section with image preview
            if (resultsSection) resultsSection.style.display = 'block';
        }
    })
    .catch(error => {
        if (loading) loading.style.display = 'none';
        if (uploadBtn) uploadBtn.disabled = false;
        console.error('Fetch error:', error);
        
        if (error.message.includes('Failed to parse JSON response')) {
            showError('Server returned invalid response format. Please try again.');
        } else {
            showError('Error uploading image: ' + error.message);
        }
    });
}

function showImagePreview(file) {
    const imagePreview = document.getElementById('imagePreview');
    const noImageMessage = document.getElementById('noImageMessage');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (imagePreview) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            }
            if (noImageMessage) noImageMessage.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
}

function clearImagePreview() {
    const imagePreview = document.getElementById('imagePreview');
    const noImageMessage = document.getElementById('noImageMessage');
    
    if (imagePreview) {
        imagePreview.src = '';
        imagePreview.style.display = 'none';
    }
    if (noImageMessage) noImageMessage.style.display = 'block';
}

function toggleImageSize() {
    const imagePreview = document.getElementById('imagePreview');
    if (imagePreview) {
        if (imagePreview.style.maxHeight === '400px' || !imagePreview.style.maxHeight) {
            imagePreview.style.maxHeight = 'none';
            imagePreview.style.maxWidth = 'none';
            imagePreview.style.cursor = 'zoom-out';
        } else {
            imagePreview.style.maxHeight = '400px';
            imagePreview.style.maxWidth = '100%';
            imagePreview.style.cursor = 'zoom-in';
        }
    }
}

function showResults(data) {
    // Store the current article data for language switching
    currentArticleData = data;
    
    // Clear previous results
    const imageAnalysis = document.getElementById('imageAnalysis');
    const articleContent = document.getElementById('articleContent');
    const metadataGrid = document.getElementById('metadataGrid');
    
    if (imageAnalysis) imageAnalysis.innerHTML = '';
    if (articleContent) articleContent.innerHTML = '';
    if (metadataGrid) metadataGrid.innerHTML = '';
    
    // Show basic image analysis results
    if (imageAnalysis) {
        imageAnalysis.innerHTML = `
            <p><strong>Caption:</strong> ${data.img_caption || 'N/A'}</p>
            <p><strong>Objects Detected:</strong> ${data.objects ? data.objects.join(', ') : 'None'}</p>
            <p><strong>Text Found:</strong> ${data.ocr_text || 'No text detected'}</p>
        `;
        if (imageAnalysis.parentElement) imageAnalysis.parentElement.style.display = 'block';
    }
    
    // Display structured article if available
    const article = data.article || {};
    if (article.title && article.body) {
        // Use the new schema with 'body' field
        let articleBody = article.body;
        
        // Show language switcher and download section
        showArticleLanguageSwitcher(data.target_language);
        showDownloadSection();
        
        // Build the structured article HTML
        const articleHTML = `
            <div class="article-header">
                <div class="article-language-indicator">
                    <span class="language-badge ${data.target_language === 'ta' ? 'tamil' : 'english'}">
                        ${data.target_language === 'ta' ? '🇮🇳 தமிழ்' : '🇺🇸 English'}
                    </span>
                </div>
                <h4 class="article-title">${article.title}</h4>
                <p class="article-subtitle">${article.subtitle || ''}</p>
            </div>
            <div class="article-body">
                ${articleBody.replace(/\n/g, '<br>')}
            </div>
            <div class="article-footer">
                <div class="article-tags">
                    <strong>Tags:</strong> ${(article.tags || []).map(tag => `<span class="tag">${tag}</span>`).join(' ')}
                </div>
                <div class="article-meta">
                    <strong>Image Caption:</strong> ${article.image_caption || 'N/A'}<br>
                    <strong>Alt Text:</strong> ${article.alt_text || 'N/A'}
                </div>
            </div>
        `;
        
        // Set the structured HTML
        if (articleContent) articleContent.innerHTML = articleHTML;
        
    } else {
        if (articleContent) articleContent.innerHTML = 'No article generated for this image.';
        // Hide language switcher and download section if no article
        const articleLanguageSwitcher = document.getElementById('articleLanguageSwitcher');
        const downloadSection = document.querySelector('.download-section');
        if (articleLanguageSwitcher) articleLanguageSwitcher.style.display = 'none';
        if (downloadSection) downloadSection.style.display = 'none';
    }

    // Display metadata
    if (metadataGrid) {
        metadataGrid.innerHTML = `
            <div class="metadata-item">
                <strong>GPS Coordinates</strong>
                <span>${data.gps ? `${data.gps.lat}°, ${data.gps.lon}°` : 'Not available'}</span>
            </div>
            <div class="metadata-item">
                <strong>Date & Time</strong>
                <span>${data.datetime || 'Not available'}</span>
            </div>
            <div class="metadata-item">
                <strong>Camera Model</strong>
                <span>${data.camera_model || 'Not available'}</span>
            </div>
        `;
    }

    // Show/hide location input based on GPS data
    const locationInputSection = document.getElementById('locationInputSection');
    if (locationInputSection) {
        if (!data.gps) {
            locationInputSection.style.display = 'block';
        } else {
            locationInputSection.style.display = 'none';
        }
    }

    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) resultsSection.style.display = 'block';
    
    // Store the uploaded photo for Day Story Creator
    storeUploadedPhoto(data);
}

function storeUploadedPhoto(data) {
    // Create a photo object for the Day Story Creator
    const photo = {
        filename: data.filename || `photo_${Date.now()}.jpg`,
        date: data.datetime ? new Date(data.datetime).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        time: data.datetime ? new Date(data.datetime).toTimeString().split(' ')[0].substring(0, 5) : new Date().toTimeString().split(' ')[0].substring(0, 5),
        daypart: getDaypartFromTime(data.datetime ? new Date(data.datetime).toTimeString().split(' ')[0] : new Date().toTimeString().split(' ')[0]),
        imageData: window.currentUploadedImageData || null, // Use the stored image data
        analysis: data // Store the full analysis data
    };
    
    uploadedPhotos.push(photo);
    console.log('Photo stored for Day Story Creator:', photo);
    console.log('Total uploaded photos:', uploadedPhotos.length);
    
    // Clear the stored image data after use
    window.currentUploadedImageData = null;
    
    // If we're currently on the Day Story Creator tab, refresh the photo grid
    const dayStoryTab = document.getElementById('day-story-tab');
    if (dayStoryTab && dayStoryTab.style.display !== 'none') {
        console.log('Refreshing photo grid for new upload...');
        loadAvailablePhotos();
    }
}

// Language switching functionality
function switchArticleLanguage(newLanguage) {
    if (!currentArticleData) {
        showError('No article data available to switch language');
        return;
    }
    
    // Show loading state
    const articleContent = document.getElementById('articleContent');
    if (articleContent) {
        articleContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Switching language...</p></div>';
    }
    
    // Call regenerate article API with new language
    const formData = new FormData();
    formData.append('target_language', newLanguage);
    formData.append('image_analysis', JSON.stringify(currentArticleData));
    
    fetch('/api/regenerate-article/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            // Update the current article data
            currentArticleData = data;
            currentArticleData.target_language = newLanguage;
            
            // Re-display results with new language
            showResults(currentArticleData);
            showSuccess('Language switched successfully!');
        }
    })
    .catch(error => {
        console.error('Error switching language:', error);
        showError('Failed to switch language. Please try again.');
    });
}

// Download functionality
function downloadArticle(format) {
    if (!currentArticleData || !currentArticleData.article) {
        showError('No article available to download');
        return;
    }
    
    const article = currentArticleData.article;
    let content = '';
    let filename = '';
    let mimeType = '';
    
    if (format === 'txt') {
        content = `${article.title}\n\n${article.subtitle || ''}\n\n${article.body}`;
        filename = 'article.txt';
        mimeType = 'text/plain';
    } else if (format === 'md') {
        content = `# ${article.title}\n\n## ${article.subtitle || ''}\n\n${article.body}`;
        filename = 'article.md';
        mimeType = 'text/markdown';
    } else if (format === 'json') {
        content = JSON.stringify(currentArticleData, null, 2);
        filename = 'article.json';
        mimeType = 'application/json';
    }
    
    if (content) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Location input functionality
let searchTimeout = null;
let currentLocation = null;

function handleLocationInput(input) {
    const value = input.value.trim();
    
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    if (value.length > 2) {
        searchTimeout = setTimeout(() => {
            searchLocation(value);
        }, 500);
    }
}

function searchLocation(query) {
    // This would integrate with a real geocoding service
    // For now, just show a placeholder
    console.log('Searching for location:', query);
}

function regenerateArticleWithLocation() {
    const locationInput = document.getElementById('locationInput');
    const location = locationInput ? locationInput.value.trim() : '';
    
    if (!location) {
        showError('Please enter a location');
        return;
    }
    
    if (!currentArticleData) {
        showError('No image analysis data available');
        return;
    }
    
    // Show loading state
    const regenerateBtn = document.querySelector('.regenerate-btn');
    if (regenerateBtn) {
        regenerateBtn.disabled = true;
        regenerateBtn.textContent = 'Regenerating...';
    }
    
    // Call regenerate article API
    const formData = new FormData();
    formData.append('target_language', currentArticleData.target_language || 'en');
    formData.append('image_analysis', JSON.stringify(currentArticleData));
    formData.append('location', location);
    
    fetch('/api/regenerate-article/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (regenerateBtn) {
            regenerateBtn.disabled = false;
            regenerateBtn.textContent = 'Regenerate Article';
        }
        
        if (data.error) {
            showError(data.error);
        } else {
            // Update the current article data
            currentArticleData = data;
            
            // Re-display results
            showResults(currentArticleData);
            showSuccess('Article regenerated with location context!');
        }
    })
    .catch(error => {
        if (regenerateBtn) {
            regenerateBtn.disabled = false;
            regenerateBtn.textContent = 'Regenerate Article';
        }
        console.error('Error regenerating article:', error);
        showError('Failed to regenerate article. Please try again.');
    });
}
