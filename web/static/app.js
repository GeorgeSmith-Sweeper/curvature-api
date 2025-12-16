/**
 * Curvature Web Interface
 * =======================
 * JavaScript to handle Google Maps integration and API communication
 */

// Global variables
let map;  // Google Maps object
let currentData = null;  // Stores the current GeoJSON data
let dataLayer = null;  // Google Maps Data Layer for displaying roads
let appConfig = null;  // Application configuration from backend

/**
 * Load configuration from backend and initialize Google Maps
 * This runs on page load
 */
async function loadConfigAndInitialize() {
    try {
        // Fetch configuration from backend
        const response = await fetch('/config');
        if (!response.ok) {
            throw new Error('Failed to load configuration');
        }

        appConfig = await response.json();
        console.log('Configuration loaded from backend');

        // Dynamically load Google Maps JavaScript API with proper async loading
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=${appConfig.google_maps_api_key}&callback=initMap&loading=async`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);

        console.log('Google Maps script loading...');
    } catch (error) {
        console.error('Error loading configuration:', error);
        alert('Failed to load map configuration. Please check that the server is running and configured correctly.');
    }
}

/**
 * Initialize Google Maps
 * This function is called automatically by Google Maps API when it loads
 * (callback is specified in the dynamically loaded script tag)
 */
function initMap() {
    // Create the map centered on Vermont (change to your preferred location)
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 44.0, lng: -72.7 },  // Vermont coordinates
        zoom: 8,
        // Optional: Use a map style that highlights roads
        mapTypeId: 'terrain'
    });

    // Create a data layer for displaying GeoJSON roads
    dataLayer = new google.maps.Data();
    dataLayer.setMap(map);

    // Style the roads based on their curvature score
    dataLayer.setStyle(function(feature) {
        const curvature = feature.getProperty('curvature');
        const color = getCurvatureColor(curvature);

        return {
            strokeColor: color,
            strokeWeight: 3,
            strokeOpacity: 0.8
        };
    });

    // Add click listener to show road details
    dataLayer.addListener('click', function(event) {
        showRoadDetails(event.feature);
    });

    console.log('Map initialized successfully');
}

/**
 * Get a color based on curvature score
 * Lower curvature = yellow, higher curvature = red
 */
function getCurvatureColor(curvature) {
    if (curvature < 600) {
        return '#FFC107';  // Yellow - mild curves
    } else if (curvature < 1000) {
        return '#FF9800';  // Orange - moderate curves
    } else if (curvature < 2000) {
        return '#F44336';  // Red - very curvy
    } else {
        return '#9C27B0';  // Purple - extremely curvy!
    }
}

/**
 * Get the CSS class for curvature badge
 */
function getCurvatureClass(curvature) {
    if (curvature < 600) return 'curvature-low';
    if (curvature < 1000) return 'curvature-medium';
    return 'curvature-high';
}

/**
 * Update the curvature slider label
 */
function updateCurvatureLabel() {
    const value = document.getElementById('min-curvature').value;
    document.getElementById('curvature-value').textContent = value;
}

/**
 * Load data from a msgpack file
 * Calls the API to load the specified file into memory
 */
async function loadData() {
    const filepath = document.getElementById('filepath').value;
    const statusDiv = document.getElementById('load-status');

    // Show loading state
    statusDiv.className = 'status loading';
    statusDiv.textContent = 'Loading data...';

    try {
        // Call the API to load data
        // fetch() is JavaScript's way of making HTTP requests
        const response = await fetch('/data/load?' + new URLSearchParams({
            filepath: filepath
        }), {
            method: 'POST'
        });

        // Check if request was successful
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Parse JSON response
        const data = await response.json();

        // Show success message
        statusDiv.className = 'status success';
        statusDiv.textContent = `✓ Loaded ${data.message}`;

        console.log('Data loaded:', data);

    } catch (error) {
        // Show error message
        statusDiv.className = 'status error';
        statusDiv.textContent = `✗ Error: ${error.message}`;
        console.error('Error loading data:', error);
    }
}

/**
 * Search for roads based on filter criteria
 * Calls the API and displays results on the map
 */
async function searchRoads() {
    const minCurvature = document.getElementById('min-curvature').value;
    const surface = document.getElementById('surface').value;
    const limit = document.getElementById('limit').value;
    const statusDiv = document.getElementById('search-status');

    // Show loading state
    statusDiv.className = 'status loading';
    statusDiv.textContent = 'Searching...';

    try {
        // Build query parameters
        const params = new URLSearchParams({
            min_curvature: minCurvature,
            limit: limit
        });

        // Add surface filter if selected
        if (surface) {
            params.append('surface', surface);
        }

        // Call the API
        const response = await fetch('/roads/geojson?' + params.toString());

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Search failed');
        }

        // Parse GeoJSON response
        const geojson = await response.json();
        currentData = geojson;

        // Display results on map
        displayRoadsOnMap(geojson);

        // Display results in sidebar list
        displayRoadsList(geojson);

        // Show success message
        statusDiv.className = 'status success';
        statusDiv.textContent = `✓ Found ${geojson.features.length} roads`;

        console.log('Search results:', geojson);

    } catch (error) {
        statusDiv.className = 'status error';
        statusDiv.textContent = `✗ Error: ${error.message}`;
        console.error('Error searching roads:', error);
    }
}

/**
 * Display roads on the Google Map
 * Takes a GeoJSON FeatureCollection and adds it to the map
 */
function displayRoadsOnMap(geojson) {
    // Clear existing roads from the map
    dataLayer.forEach(function(feature) {
        dataLayer.remove(feature);
    });

    // Add new roads
    dataLayer.addGeoJson(geojson);

    // Calculate bounds to fit all roads in view
    if (geojson.features && geojson.features.length > 0) {
        const bounds = new google.maps.LatLngBounds();

        dataLayer.forEach(function(feature) {
            feature.getGeometry().forEachLatLng(function(latLng) {
                bounds.extend(latLng);
            });
        });

        // Fit the map to show all roads
        map.fitBounds(bounds);
    }
}

/**
 * Display list of roads in the sidebar
 */
function displayRoadsList(geojson) {
    const countDiv = document.getElementById('results-count');
    const listDiv = document.getElementById('results-list');

    // Update count
    countDiv.textContent = `Showing ${geojson.features.length} roads`;

    // Clear existing list
    listDiv.innerHTML = '';

    // Sort roads by curvature (highest first)
    const sortedFeatures = geojson.features.sort((a, b) =>
        b.properties.curvature - a.properties.curvature
    );

    // Create list items
    sortedFeatures.forEach(feature => {
        const props = feature.properties;

        const item = document.createElement('div');
        item.className = 'road-item';
        item.onclick = () => zoomToRoad(feature);

        item.innerHTML = `
            <div class="road-name">${props.name}</div>
            <div class="road-stats">
                <span class="curvature-badge ${getCurvatureClass(props.curvature)}">
                    ${Math.round(props.curvature)}
                </span>
                ${props.length_mi.toFixed(1)} mi
                • ${props.surface}
            </div>
        `;

        listDiv.appendChild(item);
    });
}

/**
 * Zoom the map to show a specific road
 */
function zoomToRoad(feature) {
    const bounds = new google.maps.LatLngBounds();

    // Get all coordinates for this road
    const coords = feature.geometry.coordinates;
    coords.forEach(coord => {
        bounds.extend(new google.maps.LatLng(coord[1], coord[0]));
    });

    // Zoom to fit this road with some padding
    map.fitBounds(bounds);
    map.setZoom(Math.min(map.getZoom(), 13));  // Don't zoom in too much

    // Show road info
    showRoadDetails(feature);
}

/**
 * Show detailed information about a road
 * Opens an info window on the map
 */
function showRoadDetails(feature) {
    const props = feature.properties;

    // Create info window content
    const content = `
        <div style="max-width: 300px; font-family: sans-serif;">
            <h3 style="margin-top: 0; color: #2c3e50;">${props.name}</h3>
            <table style="width: 100%; font-size: 14px;">
                <tr>
                    <td style="padding: 4px; font-weight: 600;">Curvature:</td>
                    <td style="padding: 4px;">
                        <span class="curvature-badge ${getCurvatureClass(props.curvature)}">
                            ${Math.round(props.curvature)}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px; font-weight: 600;">Length:</td>
                    <td style="padding: 4px;">${props.length_mi.toFixed(2)} mi (${props.length_km.toFixed(2)} km)</td>
                </tr>
                <tr>
                    <td style="padding: 4px; font-weight: 600;">Surface:</td>
                    <td style="padding: 4px;">${props.surface}</td>
                </tr>
            </table>
        </div>
    `;

    // Get the center point of the road
    const coords = feature.geometry.coordinates;
    const midIndex = Math.floor(coords.length / 2);
    const center = new google.maps.LatLng(coords[midIndex][1], coords[midIndex][0]);

    // Create and show info window
    const infoWindow = new google.maps.InfoWindow({
        content: content,
        position: center
    });

    infoWindow.open(map);
}

/**
 * Initialize the interface when page loads
 */
window.addEventListener('load', function() {
    console.log('Curvature web interface loaded');
    updateCurvatureLabel();

    // Load configuration from backend and initialize Google Maps
    loadConfigAndInitialize();
});
