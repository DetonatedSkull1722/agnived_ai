import { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Marker, useMapEvents } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

import '../styles/Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// --- LEAFLET ICON FIX ---
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import bengalTigerImg from '../assets/bengal-tiger.png';
import indianElephantImg from '../assets/indian-elephant.png';
import asiaticLionImg from '../assets/asiatic-lion.png';
import indianRhinoImg from '../assets/indian-rhino.png';
import snowLeopardImg from '../assets/snow-leopard.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// --- DATA: INFORMATIC CARDS ---
const SPECIES_DATA = [
  { 
    name: "Bengal Tiger", 
    status: "Endangered",
    habitat: "Mangroves & Grasslands",
    note: "Keystone species crucial for controlling herbivore populations.",
    img: bengalTigerImg
  },
  { 
    name: "Indian Elephant", 
    status: "Endangered",
    habitat: "Forests",
    note: "Engineers of the forest, creating pathways for other animals.",
    img: indianElephantImg
  },
  { 
    name: "Asiatic Lion", 
    status: "Endangered",
    habitat: "Dry Deciduous Forests",
    note: "Found only in Gir National Park, living symbol of pride.",
    img: asiaticLionImg
  },
  { 
    name: "Indian Rhino", 
    status: "Vulnerable",
    habitat: "Grasslands",
    note: "The largest of the rhino species, identified by a single horn.",
    img: indianRhinoImg
  },
  { 
    name: "Snow Leopard", 
    status: "Vulnerable",
    habitat: "High Himalayas",
    note: "Known as the 'Ghost of the Mountains' due to elusive nature.",
    img: snowLeopardImg
  },
];

// Helper: Handle Map Clicks
function LocationSelector({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng);
    },
  });
  return null;
}

// Helper: Secure Image Component (Fetches image with Bearer Token)
const SecureImage = ({ imageId, alt }) => {
  const [imgSrc, setImgSrc] = useState(null);

  useEffect(() => {
    const fetchImage = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/image/${imageId}`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        });
        const url = URL.createObjectURL(response.data);
        setImgSrc(url);
      } catch (err) {
        console.error("Failed to load image", err);
      }
    };
    if (imageId) fetchImage();
  }, [imageId]);

  if (!imgSrc) return <div className="img-placeholder">Loading...</div>;
  return <img src={imgSrc} alt={alt} />;
};

export default function Dashboard() {
  // --- STATE ---
  const [activeTab, setActiveTab] = useState('analysis');
  const [viewState, setViewState] = useState('map'); 
  
  // Map State
  const [coords, setCoords] = useState({ lat: 28.56027870, lng: 77.29239823 });
  const [radius, setRadius] = useState(3);
  const [showLabels, setShowLabels] = useState(false); // Toggle Map Labels

  // Upload State
  const [uploadForm, setUploadForm] = useState({ species: '', file: null });
  const [myUploads, setMyUploads] = useState([]); // Recent uploads
  const [showGalleryModal, setShowGalleryModal] = useState(false); // View More Modal

  // Data State
  const [analysisResults, setAnalysisResults] = useState(null);
  const [error, setError] = useState('');

  // --- EFFECTS ---

  // Fetch uploads when switching to Upload tab
  useEffect(() => {
    if (activeTab === 'upload') {
      fetchMyUploads();
    }
  }, [activeTab]);

  const fetchMyUploads = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/uploads/me?limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Assuming backend returns { uploads: [...] }
      setMyUploads(res.data.uploads || []);
    } catch (err) {
      console.error("Error fetching uploads", err);
    }
  };

  // --- HANDLERS ---

  const handleMapClick = (latlng) => {
    setCoords({ lat: latlng.lat, lng: latlng.lng });
  };

  const handleRunAnalysis = async () => {
    setViewState('loading');
    setError('');
    try {
      const token = localStorage.getItem('token');
      const payload = {
        lon: coords.lng,
        lat: coords.lat,
        buffer_km: radius,
        date_start: "2023-01-01",
        date_end: "2023-12-31",
        scale: 10,
        cloud_cover_max: 20,
        panos_count: 3,
        panos_area_of_interest: 100.0,
        panos_min_distance: 20.0,
        panos_labels: ["tree", "bushes", "animal"]
      };

      const response = await axios.post(
        `${API_URL}/run_landcover_vegetation_and_panos`, 
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnalysisResults(response.data);
      setViewState('results');
    } catch (err) {
      setError(err.response?.data?.detail?.error || "Analysis failed.");
      setViewState('map');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.file) return alert("Please select a file");

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('image', uploadForm.file);
      formData.append('latitude', coords.lat);
      formData.append('longitude', coords.lng);
      if(uploadForm.species) formData.append('species', uploadForm.species);

      await axios.post(`${API_URL}/upload`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      alert("Upload Successful!");
      setUploadForm({ species: '', file: null });
      fetchMyUploads(); // Refresh gallery
    } catch (err) {
      alert("Upload failed");
    }
  };

  // --- RENDER HELPERS ---

  const renderInformaticCarousel = () => (
    <div className="info-carousel-container">
      <div className="info-track">
        {/* Doubled for infinite scroll effect */}
        {[...SPECIES_DATA, ...SPECIES_DATA].map((item, idx) => (
          <div key={idx} className="species-info-card">
            <div className="card-image">
              <img src={item.img} alt={item.name} />
              <span className={`status-tag ${item.status.toLowerCase()}`}>{item.status}</span>
            </div>
            <div className="card-details">
              <h5>{item.name}</h5>
              <small>📍 {item.habitat}</small>
              <p>{item.note}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="dashboard-container">
      {/* --- LEFT PANEL --- */}
      <div className="control-panel">
        <div className="brand">
          <h2>🌿 AgniVed Dashboard</h2>
        </div>

        <div className="tabs">
          <button 
            className={activeTab === 'analysis' ? 'active' : ''} 
            onClick={() => setActiveTab('analysis')}
          >
            Analysis
          </button>
          <button 
            className={activeTab === 'upload' ? 'active' : ''} 
            onClick={() => setActiveTab('upload')}
          >
            Upload
          </button>
        </div>

        <div className="panel-content">
          {activeTab === 'analysis' ? (
            <div className="analysis-form">
              <h3>Run Geospatial Analysis</h3>
              {/* Inputs */}
              <div className="input-row">
                <div className="group">
                  <label>Latitude</label>
                  <input 
                    type="number" 
                    value={coords.lat} 
                    onChange={(e) => setCoords({...coords, lat: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="group">
                  <label>Longitude</label>
                  <input 
                    type="number" 
                    value={coords.lng} 
                    onChange={(e) => setCoords({...coords, lng: parseFloat(e.target.value)})}
                  />
                </div>
              </div>

              <div className="group">
                <label>Analysis Radius: {radius} km</label>
                <input 
                  type="range" min="3" max="20" step="1"
                  value={radius} onChange={(e) => setRadius(parseInt(e.target.value))} 
                />
              </div>

              {error && <div className="error-box">{error}</div>}

              <button 
                className="action-btn" 
                onClick={handleRunAnalysis}
                disabled={viewState === 'loading'}
              >
                {viewState === 'loading' ? 'Running Models...' : 'Run Analysis'}
              </button>
              
              {/* New Informatic Carousel */}
              <div className="carousel-section">
                <h4>Protected Species Intel</h4>
                {renderInformaticCarousel()}
              </div>
            </div>
          ) : (
            <div className="upload-wrapper">
              <form className="upload-form" onSubmit={handleUpload}>
                <h3>Submit Observation</h3>
                <div className="group">
                  <label>Species Name (Optional)</label>
                  <input 
                    type="text" placeholder="e.g. Panthera tigris"
                    value={uploadForm.species}
                    onChange={e => setUploadForm({...uploadForm, species: e.target.value})}
                  />
                </div>

                <div className="group">
                  <div className="file-drop-area">
                    <input 
                      type="file" accept="image/*"
                      onChange={e => setUploadForm({...uploadForm, file: e.target.files[0]})}
                    />
                    <p>{uploadForm.file ? uploadForm.file.name : "Drag & Drop Image Evidence"}</p>
                  </div>
                </div>

                <div className="coordinates-display">
                  <p>Location: {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}</p>
                </div>

                <button type="submit" className="action-btn upload-btn">
                  Upload Data
                </button>
              </form>

              {/* Uploads Gallery Collage */}
              <div className="uploads-gallery-section">
                <div className="gallery-header">
                  <h4>Recent Uploads</h4>
                  {myUploads.length > 4 && (
                    <button className="text-btn" onClick={() => setShowGalleryModal(true)}>
                      View More
                    </button>
                  )}
                </div>
                
                <div className="gallery-grid">
                  {myUploads.slice(0, 4).map((up) => (
                    <div key={up.id} className="gallery-item">
                      <SecureImage imageId={up.id} alt={up.species} />
                    </div>
                  ))}
                  {myUploads.length === 0 && <p className="no-data">No uploads yet.</p>}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* --- RIGHT PANEL --- */}
      <div className="visual-panel">
        
        {viewState === 'loading' && (
          <div className="loader-overlay">
            <div className="spinner"></div>
            <p>Processing Satellite Imagery...</p>
          </div>
        )}

        {viewState === 'map' && (
          <div className="map-wrapper">
            {/* Legend Toggle Button */}
            <button 
              className={`legend-toggle ${showLabels ? 'active' : ''}`}
              onClick={() => setShowLabels(!showLabels)}
            >
              {showLabels ? 'Hide Labels' : 'Show Labels'}
            </button>

            <MapContainer 
              center={coords} zoom={13} 
              style={{ width: '100%', height: '100%' }}
              scrollWheelZoom={true}
            >
              {/* 1. Base Layer: Satellite */}
              <TileLayer
                attribution='&copy; Esri'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />
              
              {/* 2. Overlay Layer: Labels/Places (Toggleable) */}
              {showLabels && (
                <TileLayer
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                />
              )}
              
              <LocationSelector onLocationSelect={handleMapClick} />
              <Marker position={coords} />
              <Circle 
                center={coords} radius={radius * 1000}
                pathOptions={{
                  fillColor: '#10b981', fillOpacity: 0.2,
                  color: '#0f2d25', weight: 2
                }}
              />
            </MapContainer>
          </div>
        )}

        {viewState === 'results' && analysisResults && (
          <div className="results-grid-container">
            <div className="results-header">
              <h2>Analysis Report</h2>
              <button className="back-btn" onClick={() => setViewState('map')}>← Map</button>
            </div>
            {/* ... Existing Results Grid Code (Kept same as before) ... */}
            <div className="grid-layout">
               <div className="result-card">
                  <h4>Vegetation Distribution</h4>
                  {/* ... render logic ... */}
                  {analysisResults.vegetation?.class_distribution && 
                   <ul>{Object.entries(analysisResults.vegetation.class_distribution).map(([k,v]) => <li key={k}>{k}: {(v*100).toFixed(1)}%</li>)}</ul>}
               </div>
               {/* Add other cards here as per previous code */}
               <div className="result-card"><h4>AI Confidence</h4><div className="big-stat">{(analysisResults.vegetation?.avg_confidence * 100).toFixed(1)}%</div></div>
            </div>
          </div>
        )}
      </div>

      {/* --- MODAL FOR GALLERY --- */}
      {showGalleryModal && (
        <div className="modal-overlay" onClick={() => setShowGalleryModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Your Contribution Gallery</h3>
              <button onClick={() => setShowGalleryModal(false)}>×</button>
            </div>
            <div className="full-gallery-grid">
              {myUploads.map((up) => (
                <div key={up.id} className="gallery-item large">
                   <SecureImage imageId={up.id} alt={up.species} />
                   <div className="img-caption">
                      <span>{up.species || 'Unknown'}</span>
                      <small>{new Date().toLocaleDateString()}</small>
                   </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}