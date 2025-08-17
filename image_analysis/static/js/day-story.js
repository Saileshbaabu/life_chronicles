// Day Story Creator Functions

function loadAvailablePhotos() {
    console.log('Loading available photos...');
    
    // Use uploaded photos if available, otherwise fall back to mock data
    if (uploadedPhotos.length > 0) {
        console.log('Using uploaded photos:', uploadedPhotos.length);
        availablePhotos = uploadedPhotos.map((photo, index) => ({
            id: `uploaded_${index}`,
            filename: photo.filename || `photo_${index + 1}.jpg`,
            date: photo.date || new Date().toISOString().split('T')[0],
            time: photo.time || '12:00',
            daypart: photo.daypart || 'afternoon',
            imageData: photo.imageData, // Store the actual image data
            analysis: photo.analysis // Store the AI analysis
        }));
    } else {
        console.log('No uploaded photos, using mock data');
        // Mock data for demonstration - in real app, this would come from API
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
    const uploadedPhotoCount = document.getElementById('uploadedPhotoCount');
    if (uploadedPhotoCount) {
        uploadedPhotoCount.textContent = uploadedPhotos.length;
    }
    
    renderPhotoGrid();
}

function renderPhotoGrid() {
    console.log('Rendering photo grid...');
    const photoGrid = document.getElementById('photoGrid');
    console.log('Photo grid element:', photoGrid);
    if (!photoGrid) {
        console.error('Photo grid element not found!');
        return;
    }
    photoGrid.innerHTML = '';
    
    availablePhotos.forEach(photo => {
        console.log('Creating photo item for:', photo.filename);
        console.log('Photo data:', photo);
        console.log('Has imageData:', !!photo.imageData);
        console.log('imageData type:', typeof photo.imageData);
        console.log('imageData length:', photo.imageData ? photo.imageData.length : 'N/A');
        
        const photoItem = document.createElement('div');
        photoItem.className = `photo-item ${selectedPhotos.includes(photo.id) ? 'selected' : ''}`;
        photoItem.onclick = () => togglePhotoSelection(photo.id);
        
        const daypartColor = getDaypartColor(photo.daypart);
        
        // If we have actual image data, use it; otherwise use placeholder
        if (photo.imageData) {
            console.log('Rendering photo with image data:', photo.filename, 'imageData length:', photo.imageData.length);
            photoItem.innerHTML = `
                <img src="${photo.imageData}" alt="${photo.filename}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;" onload="console.log('Image loaded successfully:', '${photo.filename}')" onerror="console.error('Image failed to load:', '${photo.filename}', this.src)">
                <div class="photo-info">
                    <div class="photo-filename">${photo.filename}</div>
                    <div class="photo-time">${photo.time}</div>
                    <div class="daypart-badge" style="background-color: ${daypartColor}">
                        ${photo.daypart}
                    </div>
                </div>
            `;
        } else {
            console.log('Rendering photo with placeholder:', photo.filename, 'no imageData');
            photoItem.innerHTML = `
                <div class="photo-placeholder" style="background-color: ${daypartColor}; width: 100%; height: 120px; border-radius: 8px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 16px;">
                    ${photo.daypart.toUpperCase()}
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
        
        photoGrid.appendChild(photoItem);
        console.log('Photo item added to grid:', photoItem);
    });
    
    updateSelectedCount();
    console.log('Photo grid rendered successfully');
}

function togglePhotoSelection(photoId) {
    if (selectedPhotos.includes(photoId)) {
        selectedPhotos = selectedPhotos.filter(id => id !== photoId);
    } else {
        selectedPhotos.push(photoId);
    }
    
    renderPhotoGrid();
}

function updateSelectedCount() {
    const selectedCount = document.getElementById('selectedCount');
    if (selectedCount) {
        selectedCount.textContent = selectedPhotos.length;
    }
}

function createDayStory() {
    if (selectedPhotos.length === 0) {
        showError('Please select at least one photo');
        return;
    }

    const lang = document.getElementById('storyLanguage').value;
    const tone = document.getElementById('storyTone').value;
    const length = document.getElementById('storyLength').value;

    // Show loading state
    const createBtn = document.getElementById('createStoryBtn');
    const originalText = createBtn.innerHTML;
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Story...';
    }

    // Mock API call - in real app, this would call the actual stories API
    setTimeout(() => {
        // Generate mock story based on selected options
        const story = generateMockStory(selectedPhotos, lang, tone, length);
        displayGeneratedStory(story);
        
        // Reset button
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalText;
        }
    }, 2000);
}

function generateMockStory(photoIds, lang, tone, length) {
    const photos = availablePhotos.filter(p => photoIds.includes(p.id));
    const dayparts = [...new Set(photos.map(p => p.daypart))].sort();
    
    // Generate story based on language
    if (lang === 'ta') {
        return {
            title: getTamilTitle(tone, dayparts),
            subtitle: getTamilSubtitle(tone, photos.length),
            intro_md: getTamilIntro(tone, dayparts),
            sections: photos.map((photo, index) => ({
                media_id: photo.id,
                section_heading: getTamilDaypart(photo.daypart),
                body_md: getTamilSectionBody(photo, tone),
                image_caption: photo.analysis?.img_caption || `${getTamilDaypart(photo.daypart)} புகைப்படம்`,
                alt_text: `${photo.filename} - ${getTamilDaypart(photo.daypart)} நேரத்தில் எடுக்கப்பட்டது`,
                tags: [getTamilDaypart(photo.daypart), getTamilTone(tone)]
            })),
            outro_md: getTamilOutro(tone, dayparts)
        };
    } else {
        return {
            title: getEnglishTitle(tone, dayparts),
            subtitle: getEnglishSubtitle(tone, photos.length),
            intro_md: getEnglishIntro(tone, dayparts),
            sections: photos.map((photo, index) => ({
                media_id: photo.id,
                section_heading: photo.daypart.charAt(0).toUpperCase() + photo.daypart.slice(1),
                body_md: getEnglishSectionBody(photo, tone),
                image_caption: photo.analysis?.img_caption || `${photo.daypart} photo`,
                alt_text: `${photo.filename} - taken during ${photo.daypart}`,
                tags: [photo.daypart, tone]
            })),
            outro_md: getEnglishOutro(tone, dayparts)
        };
    }
}

// English story generation helpers
function getEnglishTitle(tone, dayparts) {
    const titles = {
        diary: `A ${dayparts[0]} to ${dayparts[dayparts.length - 1]} Day`,
        travelogue: `Journey Through ${dayparts.join(' and ')}`,
        reportage: `Chronicles of ${dayparts.join(', ')}`
    };
    return titles[tone] || 'My Day Story';
}

function getEnglishSubtitle(tone, photoCount) {
    const subtitles = {
        diary: `Capturing ${photoCount} moments of daily life`,
        travelogue: `Exploring life through ${photoCount} snapshots`,
        reportage: `Documenting ${photoCount} moments in time`
    };
    return subtitles[tone] || `A story in ${photoCount} photos`;
}

function getEnglishIntro(tone, dayparts) {
    const intros = {
        diary: `Today unfolded across ${dayparts.length} distinct phases, each captured in its own moment.`,
        travelogue: `From ${dayparts[0]} to ${dayparts[dayparts.length - 1]}, this journey through time reveals the beauty of everyday moments.`,
        reportage: `This collection of ${dayparts.length} time periods tells the story of a day lived fully.`
    };
    return intros[tone] || `A day documented through ${dayparts.length} different times.`;
}

function getEnglishSectionBody(photo, tone) {
    const bodies = {
        diary: `This ${photo.daypart} moment captures ${photo.filename}, a snapshot of daily life.`,
        travelogue: `During ${photo.daypart}, we find ourselves in ${photo.filename}, exploring the journey of the day.`,
        reportage: `The ${photo.daypart} brings us ${photo.filename}, documenting this moment in time.`
    };
    return bodies[tone] || `A ${photo.daypart} photo showing ${photo.filename}.`;
}

function getEnglishOutro(tone, dayparts) {
    const outros = {
        diary: `As the day concludes, these ${dayparts.length} moments remind us of life's simple beauty.`,
        travelogue: `From ${dayparts[0]} to ${dayparts[dayparts.length - 1]}, this journey has been one of discovery and wonder.`,
        reportage: `This documentation of ${dayparts.length} time periods captures the essence of a day well lived.`
    };
    return outros[tone] || `A day well documented through these ${dayparts.length} moments.`;
}

// Tamil story generation helpers
function getTamilTitle(tone, dayparts) {
    const titles = {
        diary: `${dayparts[0]} முதல் ${dayparts[dayparts.length - 1]} வரை ஒரு நாள்`,
        travelogue: `${dayparts.join(' மற்றும் ')} வழியாக பயணம்`,
        reportage: `${dayparts.join(', ')} காலங்களின் கதைகள்`
    };
    return titles[tone] || 'என் நாள் கதை';
}

function getTamilSubtitle(tone, photoCount) {
    const subtitles = {
        diary: `${photoCount} தருணங்களை பதிவு செய்து`,
        travelogue: `${photoCount} புகைப்படங்களில் வாழ்க்கையை ஆராய்ந்து`,
        reportage: `${photoCount} தருணங்களை ஆவணப்படுத்தி`
    };
    return subtitles[tone] || `${photoCount} புகைப்படங்களில் ஒரு கதை`;
}

function getTamilIntro(tone, dayparts) {
    const intros = {
        diary: `இன்று ${dayparts.length} வெவ்வேறு கட்டங்களில் விரிந்தது, ஒவ்வொன்றும் தனது சொந்த தருணத்தில் பதிவு செய்யப்பட்டது.`,
        travelogue: `${dayparts[0]} முதல் ${dayparts[dayparts.length - 1]} வரை, நேரத்தின் வழியாக இந்த பயணம் அன்றாட தருணங்களின் அழகை வெளிப்படுத்துகிறது.`,
        reportage: `${dayparts.length} கால கட்டங்களின் இந்த தொகுப்பு முழுமையாக வாழ்ந்த ஒரு நாளின் கதையை சொல்கிறது.`
    };
    return intros[tone] || `${dayparts.length} வெவ்வேறு நேரங்களில் ஆவணப்படுத்தப்பட்ட ஒரு நாள்.`;
}

function getTamilSectionBody(photo, tone) {
    const bodies = {
        diary: `இந்த ${getTamilDaypart(photo.daypart)} தருணம் ${photo.filename} ஐ பதிவு செய்கிறது, அன்றாட வாழ்க்கையின் ஒரு புகைப்படம்.`,
        travelogue: `${getTamilDaypart(photo.daypart)} நேரத்தில், நாம் ${photo.filename} இல் நம்மை காண்கிறோம், நாளின் பயணத்தை ஆராய்கிறோம்.`,
        reportage: `${getTamilDaypart(photo.daypart)} நமக்கு ${photo.filename} ஐ கொண்டு வருகிறது, நேரத்தின் இந்த தருணத்தை ஆவணப்படுத்துகிறது.`
    };
    return bodies[tone] || `${getTamilDaypart(photo.daypart)} புகைப்படம் ${photo.filename} ஐ காட்டுகிறது.`;
}

function getTamilOutro(tone, dayparts) {
    const outros = {
        diary: `நாள் முடிவடையும்போது, இந்த ${dayparts.length} தருணங்கள் வாழ்க்கையின் எளிய அழகை நமக்கு நினைவூட்டுகின்றன.`,
        travelogue: `${dayparts[0]} முதல் ${dayparts[dayparts.length - 1]} வரை, இந்த பயணம் கண்டுபிடிப்பு மற்றும் வியப்பின் ஒன்றாக இருந்தது.`,
        reportage: `${dayparts.length} கால கட்டங்களின் இந்த ஆவணப்படுத்தல் நன்கு வாழ்ந்த ஒரு நாளின் சாரத்தை பிடிக்கிறது.`
    };
    return outros[tone] || `இந்த ${dayparts.length} தருணங்களில் நன்கு ஆவணப்படுத்தப்பட்ட ஒரு நாள்.`;
}

// Tamil translation helpers
function getTamilDaypart(daypart) {
    const translations = {
        morning: 'காலை',
        afternoon: 'மதியம்',
        evening: 'மாலை',
        night: 'இரவு'
    };
    return translations[daypart] || daypart;
}

function getTamilTone(tone) {
    const translations = {
        diary: 'நாட்குறிப்பு',
        travelogue: 'பயணக் கட்டுரை',
        reportage: 'செய்தி அறிக்கை'
    };
    return translations[tone] || tone;
}

function displayGeneratedStory(story) {
    const generatedStory = document.getElementById('generatedStory');
    const storyContent = document.getElementById('storyContent');
    
    if (generatedStory && storyContent) {
        // Build the story display HTML
        const storyHTML = `
            <div class="story-header">
                <h4>${story.title}</h4>
                <p class="story-subtitle">${story.subtitle}</p>
            </div>
            <div class="story-intro">
                <p>${story.intro_md}</p>
            </div>
            <div class="story-sections">
                ${story.sections.map(section => `
                    <div class="story-section">
                        <h5>${section.section_heading}</h5>
                        <p>${section.body_md}</p>
                        <div class="section-meta">
                            <small><strong>Caption:</strong> ${section.image_caption}</small><br>
                            <small><strong>Tags:</strong> ${section.tags.join(', ')}</small>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="story-outro">
                <p>${story.outro_md}</p>
            </div>
        `;
        
        storyContent.innerHTML = storyHTML;
        generatedStory.style.display = 'block';
    }
}
