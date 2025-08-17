// Main App Variables

let currentArticleData = null;
let uploadedPhotos = [];
let availablePhotos = [];
let selectedPhotos = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Life Chronicles app initialized');
    initializeLanguageSwitcher();
    setupEventListeners();
    loadAvailablePhotos();
});

// Setup event listeners
function setupEventListeners() {
    // File input change
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                uploadImage(e.target.files[0]);
            }
        });
    }

    // Drag and drop
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('drop', handleDrop);
        uploadArea.addEventListener('click', () => fileInput.click());
    }

    // Camera functionality
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.addEventListener('click', openCamera);
    }
}

// Tab switching functionality
function showTab(tabName, event) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    console.log('Found tab contents:', tabContents.length);
    
    tabContents.forEach(tab => {
        if (tab.id === 'image-analysis-tab') {
            console.log('Hiding tab: image-analysis-tab');
            tab.style.display = 'none';
        } else if (tab.id === 'day-story-tab') {
            console.log('Hiding tab: day-story-tab');
            tab.style.display = 'none';
        }
    });
    
    // Remove active class from all tabs
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => tab.classList.remove('active'));
    
    // Show target tab content
    const targetTab = document.getElementById(tabName + '-tab');
    console.log('Target tab element:', targetTab);
    if (targetTab) {
        targetTab.style.display = 'block';
        console.log('Showing tab:', tabName + '-tab');
    }
    
    // Add active class to clicked tab
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load photos if switching to day story tab
    if (tabName === 'day-story') {
        console.log('Loading photos for day story tab');
        loadAvailablePhotos();
    }
}

// Language switcher initialization
function initializeLanguageSwitcher() {
    const switcher = document.getElementById('articleLanguageSwitcher');
    const currentLanguageText = document.getElementById('currentLanguageText');
    
    if (switcher && currentLanguageText) {
        console.log('Language switcher elements initialized successfully');
    } else {
        console.warn('Some language switcher elements not found');
    }
}

// Show language switcher
function showArticleLanguageSwitcher(currentLanguage) {
    const switcher = document.getElementById('articleLanguageSwitcher');
    const currentLanguageText = document.getElementById('currentLanguageText');
    
    if (switcher && currentLanguageText) {
        currentLanguageText.textContent = currentLanguage === 'ta' ? '🇮🇳 தமிழ்' : '🇺🇸 English';
        switcher.style.display = 'block';
    }
}

// Show download section
function showDownloadSection() {
    const downloadSection = document.querySelector('.download-section');
    if (downloadSection) {
        downloadSection.style.display = 'block';
    }
}

// Show success message
function showSuccess(message) {
    const successMessage = document.getElementById('successMessage');
    if (successMessage) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 5000);
    }
}

// Show error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
}

// Handle drag over
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

// Handle drop
function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadImage(files[0]);
    }
}

// Camera functionality
function openCamera() {
    const modal = document.getElementById('cameraModal');
    if (modal) {
        modal.style.display = 'block';
        
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                const video = document.getElementById('cameraVideo');
                if (video) {
                    video.srcObject = stream;
                    video.play();
                }
            })
            .catch(err => {
                console.error('Error accessing camera:', err);
                showError('Could not access camera. Please check permissions.');
            });
    }
}

function closeCamera() {
    const modal = document.getElementById('cameraModal');
    if (modal) {
        modal.style.display = 'none';
        
        const video = document.getElementById('cameraVideo');
        if (video && video.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
        }
    }
}

function capturePhoto() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (video && context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        canvas.toBlob(blob => {
            const file = new File([blob], 'camera_photo.jpg', { type: 'image/jpeg' });
            uploadImage(file);
            closeCamera();
        }, 'image/jpeg');
    }
}

// Utility functions
function getDaypartColor(daypart) {
    const colors = {
        morning: '#4CAF50',
        afternoon: '#FF9800',
        evening: '#9C27B0',
        night: '#2196F3'
    };
    return colors[daypart] || '#666';
}

function getDaypartFromTime(timeStr) {
    const hour = parseInt(timeStr.split(':')[0]);
    if (hour >= 5 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 21) return 'evening';
    return 'night';
}
