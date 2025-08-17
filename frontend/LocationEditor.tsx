import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './LocationEditor.css';

// Fix Leaflet marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface PlaceCandidate {
    label: string;
    lat: number;
    lon: number;
    place_name: string;
    city: string;
    admin: string;
    country: string;
    country_code: string;
    provider: string;
    provider_place_id: string;
    confidence: number;
}

interface LocationData {
    lat: number;
    lon: number;
    place_name?: string;
    city?: string;
    admin?: string;
    country?: string;
    country_code?: string;
}

interface LocationEditorProps {
    storyId: string;
    onLocationUpdate?: (location: LocationData) => void;
    initialLocation?: LocationData;
}

const LocationEditor: React.FC<LocationEditorProps> = ({
    storyId,
    onLocationUpdate,
    initialLocation
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<PlaceCandidate[]>([]);
    const [showResults, setShowResults] = useState(false);
    const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(
        initialLocation || null
    );
    const [mapCenter, setMapCenter] = useState<[number, number]>([40.7128, -74.0060]); // NYC default
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    
    const searchTimeoutRef = useRef<NodeJS.Timeout>();
    const searchInputRef = useRef<HTMLInputElement>(null);

    // Initialize map center from initial location
    useEffect(() => {
        if (initialLocation?.lat && initialLocation?.lon) {
            setMapCenter([initialLocation.lat, initialLocation.lon]);
        }
    }, [initialLocation]);

    // Debounced search
    const performSearch = useCallback(async (query: string) => {
        if (!query.trim() || query.length < 2) {
            setSearchResults([]);
            setShowResults(false);
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            
            const response = await fetch('/api/geocode/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query.trim() }),
            });

            if (!response.ok) {
                throw new Error('Search failed');
            }

            const results = await response.json();
            setSearchResults(results);
            setShowResults(results.length > 0);
        } catch (err) {
            setError('Search failed. Please try again.');
            setSearchResults([]);
            setShowResults(false);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Handle search input changes
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const query = e.target.value;
        setSearchQuery(query);
        setError(null);

        // Clear previous timeout
        if (searchTimeoutRef.current) {
            clearTimeout(searchTimeoutRef.current);
        }

        // Set new timeout for debounced search
        searchTimeoutRef.current = setTimeout(() => {
            performSearch(query);
        }, 300);
    };

    // Handle search result selection
    const handleResultSelect = (result: PlaceCandidate) => {
        setSelectedLocation({
            lat: result.lat,
            lon: result.lon,
            place_name: result.place_name,
            city: result.city,
            admin: result.admin,
            country: result.country,
            country_code: result.country_code,
        });
        
        setMapCenter([result.lat, result.lon]);
        setSearchQuery(result.label);
        setShowResults(false);
        setError(null);
    };

    // Handle map marker drag
    const handleMarkerDrag = useCallback(async (lat: number, lon: number) => {
        try {
            const response = await fetch('/api/geocode/reverse/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ lat, lon }),
            });

            if (response.ok) {
                const result = await response.json();
                setSelectedLocation({
                    lat: result.lat,
                    lon: result.lon,
                    place_name: result.place_name,
                    city: result.city,
                    admin: result.admin,
                    country: result.country,
                    country_code: result.country_code,
                });
            }
        } catch (err) {
            // Silently handle reverse geocoding errors
            setSelectedLocation(prev => prev ? { ...prev, lat, lon } : { lat, lon });
        }
    }, []);

    // Use current location
    const useCurrentLocation = () => {
        if (!navigator.geolocation) {
            setError('Geolocation is not supported by your browser');
            return;
        }

        setIsLoading(true);
        setError(null);

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                setMapCenter([latitude, longitude]);
                handleMarkerDrag(latitude, longitude);
                setIsLoading(false);
            },
            (err) => {
                setError('Unable to get your location. Please check permissions.');
                setIsLoading(false);
            }
        );
    };

    // Save location
    const saveLocation = async () => {
        if (!selectedLocation) {
            setError('Please select a location first');
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            setSuccess(null);

            const response = await fetch(`/api/stories/${storyId}/location/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(selectedLocation),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save location');
            }

            const result = await response.json();
            setSuccess('Location saved successfully!');
            
            // Update selected location with server response
            setSelectedLocation({
                lat: result.lat,
                lon: result.lon,
                place_name: result.place_name,
                city: result.city,
                admin: result.admin,
                country: result.country,
                country_code: result.country_code,
            });

            // Notify parent component
            if (onLocationUpdate) {
                onLocationUpdate(result);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save location');
        } finally {
            setIsLoading(false);
        }
    };

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            setShowResults(false);
        }
    };

    return (
        <div className="location-editor">
            <h3>Add Location Context</h3>
            
            {/* Search Input */}
            <div className="search-container">
                <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Search for a place, city, or landmark..."
                    value={searchQuery}
                    onChange={handleSearchChange}
                    onKeyDown={handleKeyDown}
                    className="search-input"
                    disabled={isLoading}
                />
                
                {isLoading && <div className="search-spinner" />}
                
                {/* Search Results Dropdown */}
                {showResults && (
                    <div className="search-results">
                        {searchResults.map((result, index) => (
                            <div
                                key={result.provider_place_id}
                                className="search-result-item"
                                onClick={() => handleResultSelect(result)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        e.preventDefault();
                                        handleResultSelect(result);
                                    }
                                }}
                                tabIndex={0}
                                role="button"
                                aria-label={`Select ${result.label}`}
                            >
                                <div className="result-label">{result.label}</div>
                                <div className="result-details">
                                    {result.city && <span>{result.city}</span>}
                                    {result.admin && <span>{result.admin}</span>}
                                    {result.country && <span>{result.country}</span>}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Map */}
            <div className="map-container">
                <MapContainer
                    center={mapCenter}
                    zoom={13}
                    style={{ height: '300px', width: '100%' }}
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    
                    {/* Draggable Marker */}
                    {selectedLocation && (
                        <DraggableMarker
                            position={[selectedLocation.lat, selectedLocation.lon]}
                            onDragEnd={handleMarkerDrag}
                        />
                    )}
                </MapContainer>
            </div>

            {/* Location Details Form */}
            <div className="location-form">
                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="city">City</label>
                        <input
                            id="city"
                            type="text"
                            value={selectedLocation?.city || ''}
                            onChange={(e) => setSelectedLocation(prev => 
                                prev ? { ...prev, city: e.target.value } : { lat: 0, lon: 0, city: e.target.value }
                            )}
                            placeholder="City name"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="country">Country</label>
                        <input
                            id="country"
                            type="text"
                            value={selectedLocation?.country || ''}
                            onChange={(e) => setSelectedLocation(prev => 
                                prev ? { ...prev, country: e.target.value } : { lat: 0, lon: 0, country: e.target.value }
                            )}
                            placeholder="Country name"
                        />
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="lat">Latitude</label>
                        <input
                            id="lat"
                            type="number"
                            step="any"
                            value={selectedLocation?.lat || ''}
                            onChange={(e) => setSelectedLocation(prev => 
                                prev ? { ...prev, lat: parseFloat(e.target.value) || 0 } : { lat: parseFloat(e.target.value) || 0, lon: 0 }
                            )}
                            placeholder="Latitude"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label htmlFor="lon">Longitude</label>
                        <input
                            id="lon"
                            type="number"
                            step="any"
                            value={selectedLocation?.lon || ''}
                            onChange={(e) => setSelectedLocation(prev => 
                                prev ? { ...prev, lon: parseFloat(e.target.value) || 0 } : { lat: 0, lon: parseFloat(e.target.value) || 0 }
                            )}
                            placeholder="Longitude"
                        />
                    </div>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="action-buttons">
                <button
                    type="button"
                    onClick={useCurrentLocation}
                    disabled={isLoading}
                    className="btn btn-secondary"
                >
                    📍 Use My Location
                </button>
                
                <button
                    type="button"
                    onClick={saveLocation}
                    disabled={!selectedLocation || isLoading}
                    className="btn btn-primary"
                >
                    {isLoading ? 'Saving...' : 'Save Location'}
                </button>
            </div>

            {/* Status Messages */}
            {error && (
                <div className="error-message" role="alert">
                    {error}
                </div>
            )}
            
            {success && (
                <div className="success-message" role="alert">
                    {success}
                </div>
            )}
        </div>
    );
};

// Draggable Marker Component
interface DraggableMarkerProps {
    position: [number, number];
    onDragEnd: (lat: number, lon: number) => void;
}

const DraggableMarker: React.FC<DraggableMarkerProps> = ({ position, onDragEnd }) => {
    const markerRef = useRef<L.Marker>(null);

    const map = useMapEvents({
        dragend: () => {
            if (markerRef.current) {
                const marker = markerRef.current;
                const { lat, lng } = marker.getLatLng();
                onDragEnd(lat, lng);
            }
        },
    });

    return (
        <Marker
            ref={markerRef}
            position={position}
            draggable={true}
            eventHandlers={{
                dragend: () => {
                    if (markerRef.current) {
                        const marker = markerRef.current;
                        const { lat, lng } = marker.getLatLng();
                        onDragEnd(lat, lng);
                    }
                },
            }}
        />
    );
};

export default LocationEditor;
