// --- CONFIGURATION ---
const API_URL = 'http://127.0.0.1:8000/api/recommendations'; 
window.travelData = null; // Global storage for fetched data

const pageContent = document.getElementById('page-content');
const navLinks = document.querySelectorAll('.nav-links a');

// --- LANDING PAGE TRANSITION ---
function enterApp() {
    const landing = document.getElementById('landing-page');
    const appInterface = document.getElementById('app-interface');
    
    // Slide Landing Page Up
    landing.style.transform = 'translateY(-100vh)';
    
    // Reveal App Interface with a slight delay for smoothness
    setTimeout(() => {
        appInterface.style.display = 'flex';
        // Trigger CSS fade-in
        setTimeout(() => {
            appInterface.style.opacity = '1';
        }, 50);
    }, 500);
}

// --- TEMPLATES ---

// 1. Home Page Renderer (Dynamic Function)
const renderHome = () => {
    const data = window.travelData;

    // SCENARIO A: Default View (User hasn't scanned yet)
    if (!data) {
        return `
        <div class="hero" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h1>Where to next?</h1>
            <p>Plan your trip manually or explore your current location.</p>
            <button onclick="document.querySelector('[data-page=\\'ai-guide\\']').click()" style="background:white; color:#764ba2; border:none; padding:12px 30px; border-radius:30px; font-weight:bold; margin-top:20px; cursor:pointer;">
                Start Planning
            </button>
        </div>
        `;
    }

    // SCENARIO B: City Dashboard (After Scan/Search)
    const cityImage = data.location_info.image || 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1350&q=80';
    
    return `
        <div class="hero fade-in" style="background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6)), url('${cityImage}'); background-size: cover; background-position: center;">
            <span style="background:rgba(255,255,255,0.2); backdrop-filter:blur(5px); padding:5px 15px; border-radius:20px; font-size:0.9rem; letter-spacing:1px; text-transform:uppercase;">
                ${data.location_info.city === "Unknown Location" ? "Detected Location" : "Destination"}
            </span>
            <h1 style="margin-top:10px;">${data.location_info.city}</h1>
            <p style="font-size:1.2rem;">${data.weather.condition} &bull; ${data.weather.temp}°C</p>
        </div>

        <div class="about-section fade-in">
            <div class="about-card">
                <h2 style="margin-bottom:15px;">Overview</h2>
                <p style="color:#64748b; line-height:1.7;">${data.location_info.history}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card weather">
                    <div>
                        <div style="font-size:0.9rem; opacity:0.8;">Temperature</div>
                        <div style="font-size:2rem; font-weight:700;">${data.weather.temp}°</div>
                    </div>
                    <i class="fa-solid fa-sun" style="font-size:2.5rem; opacity:0.5;"></i>
                </div>
                <div class="stat-card currency">
                    <div>
                        <div style="font-size:0.9rem; opacity:0.8;">Currency</div>
                        <div style="font-size:1.5rem; font-weight:700;">${data.currency.currency}</div>
                        <small>${data.currency.message}</small>
                    </div>
                    <i class="fa-solid fa-coins" style="font-size:2.5rem; opacity:0.5;"></i>
                </div>
            </div>
        </div>

        <h2 style="margin-top:40px;">Explore Categories</h2>
        <div class="card-grid">
            <div onclick="document.querySelector('[data-page=\\'hotels\\']').click()" class="card clickable">
                <div class="card-icon"><i class="fa-solid fa-hotel"></i></div>
                <h3>Hotels</h3>
                <p style="color:#64748b;">${data.hotels.length} Options available</p>
            </div>
            <div onclick="document.querySelector('[data-page=\\'food\\']').click()" class="card clickable">
                <div class="card-icon"><i class="fa-solid fa-utensils"></i></div>
                <h3>Food</h3>
                <p style="color:#64748b;">${data.food.length} Top spots</p>
            </div>
            <div onclick="document.querySelector('[data-page=\\'transport\\']').click()" class="card clickable">
                <div class="card-icon"><i class="fa-solid fa-train"></i></div>
                <h3>Transport</h3>
                <p style="color:#64748b;">Public transit info</p>
            </div>
        </div>
    `;
};

// 2. Loading State Template
const renderLoading = () => `
    <div style="text-align:center; padding:50px;">
        <i class="fa-solid fa-spinner fa-spin" style="font-size:3rem; color:#3b82f6;"></i>
        <h3 style="margin-top:20px; color:#64748b;">AI is analyzing location data...</h3>
    </div>
    <div class="card-grid" style="margin-top:30px;">
        <div class="skeleton-card skeleton"></div>
        <div class="skeleton-card skeleton"></div>
        <div class="skeleton-card skeleton"></div>
    </div>
`;

// 3. Category Templates
const templates = {
    'home': renderHome,
    'hotels': `<h2>Nearby Hotels</h2><div id="hotel-list" class="card-grid"></div>`,
    'food': `<h2>Famous Food</h2><div id="food-list" class="card-grid"></div>`,
    'transport': `<h2>Public Transport</h2><div id="transport-list" class="card-grid"></div>`,
    'safety': `<h2>Emergency & Health</h2><div id="safety-list" class="card-grid"></div>`,
    'rentacar': `<h2>Rent a Car</h2><div id="rental-list" class="card-grid"></div>`,
    
    // Updated AI Guide with Search Bar AND Location Button
    'ai-guide': `
    <div class="ai-container" style="text-align:center; padding:50px 20px;">
        <i class="fa-solid fa-earth-americas" style="font-size:3.5rem; color:#3b82f6; margin-bottom:15px; display:inline-block; animation:float 3s ease-in-out infinite;"></i>
        <h2 style="font-size:2.2rem; margin-bottom:10px;">Plan Your Trip</h2>
        <p style="color:#64748b; margin-bottom:30px; font-size:1.1rem;">Search for a city or use your GPS location.</p>
        
        <div class="search-group">
            <input type="text" id="cityInput" class="search-input" placeholder="Type a city (e.g., Paris, Tokyo)...">
            <button id="searchBtn" class="search-btn"><i class="fa-solid fa-magnifying-glass"></i></button>
        </div>

        <div class="or-divider">OR</div>

        <button id="recommendBtn" class="location-btn">
            <i class="fa-solid fa-location-crosshairs"></i> Get My Current Location
        </button>
        
        <div id="statusMessage" style="margin-top:20px; font-weight:600; min-height:24px;"></div>
    </div>
`
};

// --- NAVIGATION LOGIC ---
function loadPage(pageName) {
    // Render Content based on template type (function vs string)
    if (typeof templates[pageName] === 'function') {
        pageContent.innerHTML = templates[pageName]();
    } else if (templates[pageName]) {
        pageContent.innerHTML = templates[pageName];
    } else { return; }

    // Update Navigation Active States
    navLinks.forEach(link => {
        link.classList.remove('active');
        // Reset dropdown parents
        const parent = link.closest('.dropdown');
        if (parent) parent.querySelector('.dropbtn').style.color = '';

        // Highlight matching link
        if(link.getAttribute('data-page') === pageName) {
            link.classList.add('active');
            // If link is inside dropdown, highlight the parent "Explore" text
            if (parent) parent.querySelector('.dropbtn').style.color = 'var(--primary)';
        }
    });

    // Attach Event Listeners for AI Guide Page
    if (pageName === 'ai-guide') {
        document.getElementById('recommendBtn').addEventListener('click', getLocation);
        document.getElementById('searchBtn').addEventListener('click', searchCity);
        // Allow "Enter" key for search
        document.getElementById('cityInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') searchCity();
        });
    }

    // Inject Data into Category Tabs if data exists
    if (window.travelData) {
        if (pageName === 'hotels') renderCategory('hotel-list', window.travelData.hotels, 'fa-bed');
        if (pageName === 'food') renderCategory('food-list', window.travelData.food, 'fa-burger');
        if (pageName === 'rentacar') renderCategory('rental-list', window.travelData.rentacar, 'fa-car');
        if (pageName === 'safety') renderCategory('safety-list', window.travelData.safety, 'fa-hospital');
        if (pageName === 'transport') renderCategory('transport-list', window.travelData.transport, 'fa-train');
    }
}

// --- CARD RENDERER ---
function renderCategory(containerId, items, icon) {
    const container = document.getElementById(containerId);
    if (!container || !items) return;
    if (items.length === 0) { container.innerHTML = '<div class="card"><p>No data found.</p></div>'; return; }
    
    container.innerHTML = items.map(item => {
        // Fix: Use Standard Google Maps Query URL
        let mapLink = '#';
        if (item.latitude && item.longitude) {
            mapLink = `https://www.google.com/maps?q=${item.latitude},${item.longitude}`;
        } else {
            mapLink = `https://www.google.com/maps?q=${encodeURIComponent(item.name)}`;
        }

        return `
        <div class="card fade-in">
            <div class="card-icon"><i class="fa-solid ${icon}"></i></div>
            <h3>${item.name}</h3>
            <p style="color:#64748b; margin-bottom:15px;">${item.description}</p>
            <div style="font-weight:700; color:#3b82f6; margin-bottom:15px;">${item.price}</div>
            <a href="${mapLink}" target="_blank" class="direction-btn">
                <i class="fa-solid fa-location-arrow"></i> Navigate
            </a>
        </div>`;
    }).join('');
}

// --- API HANDLING ---

// 1. Fetch from Python Backend
async function fetchRecommendations(lat, lon) {
    // Show loading skeleton
    pageContent.innerHTML = renderLoading();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ latitude: lat, longitude: lon }),
        });

        if (!response.ok) throw new Error("API Connection Failed");
        
        // Success: Store data and redirect to Home Dashboard
        window.travelData = await response.json();
        loadPage('home'); 

    } catch (error) {
        // Error: Return to AI Guide and show message
        loadPage('ai-guide'); 
        setStatus("Error: Is the backend server running?", true);
        console.error(error);
    }
}

// 2. Geocoding (City Name -> Coordinates)
async function searchCity() {
    const input = document.getElementById('cityInput');
    const query = input.value.trim();
    if (!query) return setStatus("Please enter a city name.", true);

    setStatus("Searching for city...", false);
    
    try {
        // Use OSM Nominatim to get lat/lon from city name
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data && data.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lon = parseFloat(data[0].lon);
            // Pass coordinates to backend
            fetchRecommendations(lat, lon);
        } else {
            setStatus("City not found. Try again.", true);
        }
    } catch (error) {
        setStatus("Error finding city. Check internet.", true);
    }
}

// 3. GPS Location
function getLocation() {
    if (!navigator.geolocation) return setStatus("Geolocation not supported", true);
    
    const btn = document.getElementById('recommendBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Locating...';
    
    navigator.geolocation.getCurrentPosition(
        (pos) => fetchRecommendations(pos.coords.latitude, pos.coords.longitude),
        (err) => { 
            setStatus("Permission denied or location unavailable.", true); 
            btn.disabled = false; 
            btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Get My Current Location'; 
        }
    );
}

function setStatus(msg, isError) {
    const el = document.getElementById('statusMessage');
    if (el) { el.textContent = msg; el.style.color = isError ? '#ef4444' : '#10b981'; }
}

// --- INITIALIZATION ---
// Global Click Handler for Nav Links (avoids conflict with dropdown hover)
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        const page = e.target.getAttribute('data-page') || e.target.closest('a')?.getAttribute('data-page');
        if (page) {
            e.preventDefault();
            loadPage(page);
        }
    });
});

// Start the app at Home
loadPage('home');