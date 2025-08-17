import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LocationEditor from './LocationEditor';

// Mock fetch
global.fetch = jest.fn();

// Mock react-leaflet components
jest.mock('react-leaflet', () => ({
    MapContainer: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="map-container">{children}</div>
    ),
    TileLayer: () => <div data-testid="tile-layer" />,
    Marker: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="marker">{children}</div>
    ),
    useMapEvents: () => ({}),
}));

// Mock Leaflet
jest.mock('leaflet', () => ({
    Icon: {
        Default: {
            prototype: {},
            mergeOptions: jest.fn(),
        },
    },
}));

const mockPlaceCandidate = {
    label: "The John F. Kennedy Center for the Performing Arts, Washington, District of Columbia, United States",
    lat: 38.8951,
    lon: -77.0540,
    place_name: "The John F. Kennedy Center for the Performing Arts",
    city: "Washington",
    admin: "District of Columbia",
    country: "United States",
    country_code: "US",
    provider: "nominatim",
    provider_place_id: "123456789",
    confidence: 0.92
};

describe('LocationEditor', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders without crashing', () => {
        render(<LocationEditor storyId="test123" />);
        expect(screen.getByText('Add Location Context')).toBeInTheDocument();
    });

    it('displays search input with placeholder', () => {
        render(<LocationEditor storyId="test123" />);
        expect(screen.getByPlaceholderText('Search for a place, city, or landmark...')).toBeInTheDocument();
    });

    it('shows map container', () => {
        render(<LocationEditor storyId="test123" />);
        expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });

    it('displays form fields', () => {
        render(<LocationEditor storyId="test123" />);
        expect(screen.getByLabelText('City')).toBeInTheDocument();
        expect(screen.getByLabelText('Country')).toBeInTheDocument();
        expect(screen.getByLabelText('Latitude')).toBeInTheDocument();
        expect(screen.getByLabelText('Longitude')).toBeInTheDocument();
    });

    it('shows action buttons', () => {
        render(<LocationEditor storyId="test123" />);
        expect(screen.getByText('📍 Use My Location')).toBeInTheDocument();
        expect(screen.getByText('Save Location')).toBeInTheDocument();
    });

    it('handles search input changes', async () => {
        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        expect(searchInput).toHaveValue('Kennedy Center');
    });

    it('performs search when query is entered', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [mockPlaceCandidate]
        });

        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/geocode/search/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: 'Kennedy Center' })
            });
        });
    });

    it('displays search results', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [mockPlaceCandidate]
        });

        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        await waitFor(() => {
            expect(screen.getByText(mockPlaceCandidate.label)).toBeInTheDocument();
        });
    });

    it('handles search result selection', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [mockPlaceCandidate]
        });

        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        await waitFor(() => {
            const resultItem = screen.getByText(mockPlaceCandidate.label);
            fireEvent.click(resultItem);
        });

        // Check if form fields are populated
        expect(screen.getByDisplayValue('Washington')).toBeInTheDocument();
        expect(screen.getByDisplayValue('United States')).toBeInTheDocument();
        expect(screen.getByDisplayValue('38.8951')).toBeInTheDocument();
        expect(screen.getByDisplayValue('-77.0540')).toBeInTheDocument();
    });

    it('handles save location', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                place_str: "The John F. Kennedy Center for the Performing Arts, Washington, United States",
                lat: 38.8951,
                lon: -77.0540,
                city: "Washington",
                country: "United States",
                confidence: 0.9,
                source: "user_form"
            })
        });

        render(<LocationEditor storyId="test123" />);
        
        // Fill in required fields
        const cityInput = screen.getByLabelText('City');
        const countryInput = screen.getByLabelText('Country');
        
        fireEvent.change(cityInput, { target: { value: 'Washington' } });
        fireEvent.change(countryInput, { target: { value: 'United States' } });
        
        const saveButton = screen.getByText('Save Location');
        fireEvent.click(saveButton);
        
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/stories/test123/location/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    city: 'Washington',
                    country: 'United States',
                    lat: 0,
                    lon: 0
                })
            });
        });
    });

    it('shows error message on save failure', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            json: async () => ({ error: 'Validation failed' })
        });

        render(<LocationEditor storyId="test123" />);
        
        // Fill in required fields
        const cityInput = screen.getByLabelText('City');
        const countryInput = screen.getByLabelText('Country');
        
        fireEvent.change(cityInput, { target: { value: 'Washington' } });
        fireEvent.change(countryInput, { target: { value: 'United States' } });
        
        const saveButton = screen.getByText('Save Location');
        fireEvent.click(saveButton);
        
        await waitFor(() => {
            expect(screen.getByText('Validation failed')).toBeInTheDocument();
        });
    });

    it('disables save button when no location is selected', () => {
        render(<LocationEditor storyId="test123" />);
        const saveButton = screen.getByText('Save Location');
        expect(saveButton).toBeDisabled();
    });

    it('enables save button when location is selected', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [mockPlaceCandidate]
        });

        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        await waitFor(() => {
            const resultItem = screen.getByText(mockPlaceCandidate.label);
            fireEvent.click(resultItem);
        });

        const saveButton = screen.getByText('Save Location');
        expect(saveButton).not.toBeDisabled();
    });

    it('handles keyboard navigation in search results', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [mockPlaceCandidate]
        });

        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        await waitFor(() => {
            const resultItem = screen.getByText(mockPlaceCandidate.label);
            
            // Test Enter key
            fireEvent.keyDown(resultItem, { key: 'Enter' });
            expect(screen.getByDisplayValue('Washington')).toBeInTheDocument();
        });
    });

    it('closes search results on Escape key', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => [mockPlaceCandidate]
        });

        render(<LocationEditor storyId="test123" />);
        const searchInput = screen.getByPlaceholderText('Search for a place, city, or landmark...');
        
        fireEvent.change(searchInput, { target: { value: 'Kennedy Center' } });
        
        await waitFor(() => {
            expect(screen.getByText(mockPlaceCandidate.label)).toBeInTheDocument();
        });

        fireEvent.keyDown(searchInput, { key: 'Escape' });
        
        await waitFor(() => {
            expect(screen.queryByText(mockPlaceCandidate.label)).not.toBeInTheDocument();
        });
    });

    it('calls onLocationUpdate callback when location is saved', async () => {
        const mockCallback = jest.fn();
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                place_str: "The John F. Kennedy Center for the Performing Arts, Washington, United States",
                lat: 38.8951,
                lon: -77.0540,
                city: "Washington",
                country: "United States",
                confidence: 0.9,
                source: "user_form"
            })
        });

        render(<LocationEditor storyId="test123" onLocationUpdate={mockCallback} />);
        
        // Fill in required fields
        const cityInput = screen.getByLabelText('City');
        const countryInput = screen.getByLabelText('Country');
        
        fireEvent.change(cityInput, { target: { value: 'Washington' } });
        fireEvent.change(countryInput, { target: { value: 'United States' } });
        
        const saveButton = screen.getByText('Save Location');
        fireEvent.click(saveButton);
        
        await waitFor(() => {
            expect(mockCallback).toHaveBeenCalledWith({
                place_str: "The John F. Kennedy Center for the Performing Arts, Washington, United States",
                lat: 38.8951,
                lon: -77.0540,
                city: "Washington",
                country: "United States",
                confidence: 0.9,
                source: "user_form"
            });
        });
    });
});
