"use client";

import React, { useState, useEffect } from 'react';
import { MapPin, Satellite, Leaf, Video, Download, Settings, Sun, Moon, Activity, Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

// Utility function for class names
const cn = (...classes: string[]) => classes.filter(Boolean).join(' ');

// Main Dashboard Component
export default function AgniVedDashboard() {
  const [theme, setTheme] = useState('dark');
  const [activeTab, setActiveTab] = useState('landcover');
  const [aoi, setAoi] = useState({ lon: 77.5946, lat: 12.9716, buffer_km: 1.2 });
  type LogEntry = { time: string; message: string };
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [jobs, setJobs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  type LandcoverResults = {
    type: string;
    files: string[];
    stats: {
      [key: string]: { area: number; pct: number }
    }
  };
  const [results, setResults] = useState<LandcoverResults | null>(null);
  
  // Simulated API calls
  const runLandcover = async () => {
    setIsRunning(true);
    addLog('Starting landcover pipeline...');
    addLog(`AOI: ${aoi.lon.toFixed(4)}, ${aoi.lat.toFixed(4)} (${aoi.buffer_km}km)`);
    
    setTimeout(() => {
      addLog('✓ Downloading Sentinel-2 imagery...');
      setTimeout(() => {
        addLog('✓ Processing Dynamic World classification...');
        setTimeout(() => {
          addLog('✓ Generating vegetation mask...');
          setTimeout(() => {
            addLog('✓ Creating visualizations...');
            setIsRunning(false);
            setResults({
              type: 'landcover',
              files: [
                'sentinel2_hyperspectral.tif',
                'land_cover_classification.tif',
                'agnived_cover_analysis.png',
                'vegetation_mask.tif'
              ],
              stats: {
                water: { area: 0.15, pct: 8.3 },
                trees: { area: 0.82, pct: 45.6 },
                grass: { area: 0.31, pct: 17.2 },
                crops: { area: 0.22, pct: 12.2 },
                built: { area: 0.30, pct: 16.7 }
              }
            });
            addLog('✅ Pipeline complete!');
          }, 1500);
        }, 1500);
      }, 1500);
    }, 1000);
  };
  const addLog = (message: string) => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message }]);
  };

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-slate-950 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* Header */}
      <header className={`border-b ${theme === 'dark' ? 'border-slate-800 bg-slate-900/80' : 'border-gray-200 bg-white/80'} backdrop-blur-sm sticky top-0 z-50`}>
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-blue-600 flex items-center justify-center">
                <Satellite className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">AgniVed</h1>
                <p className="text-xs text-slate-400">Geospatial & Wildlife Analysis</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <nav className="hidden md:flex items-center gap-1">
                {[
                  { id: 'landcover', label: 'Land Cover', icon: MapPin },
                  { id: 'vegetation', label: 'Vegetation', icon: Leaf },
                  { id: 'wildlife', label: 'Wildlife', icon: Video }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      'px-4 py-2 rounded-lg flex items-center gap-2 transition-all',
                      activeTab === tab.id
                        ? theme === 'dark' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-blue-500 text-white'
                        : theme === 'dark'
                          ? 'text-slate-400 hover:text-white hover:bg-slate-800'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    )}
                  >
                    <tab.icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{tab.label}</span>
                  </button>
                ))}
              </nav>
              
              <div className="flex items-center gap-3">
                <div className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 ${
                  theme === 'dark' ? 'bg-green-500/20 text-green-400' : 'bg-green-100 text-green-700'
                }`}>
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  Connected
                </div>
                
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className={`p-2 rounded-lg transition-colors ${
                    theme === 'dark' ? 'hover:bg-slate-800' : 'hover:bg-gray-100'
                  }`}
                >
                  {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
                
                <button className={`p-2 rounded-lg transition-colors ${
                  theme === 'dark' ? 'hover:bg-slate-800' : 'hover:bg-gray-100'
                }`}>
                  <Settings className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Column - Map & Controls (60%) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Map */}
            <div className={`rounded-2xl overflow-hidden shadow-xl ${
              theme === 'dark' ? 'bg-slate-900 border border-slate-800' : 'bg-white border border-gray-200'
            }`}>
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h2 className="font-semibold flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-blue-500" />
                  Area of Interest
                </h2>
                <span className="text-sm text-slate-400">
                  {(Math.PI * Math.pow(aoi.buffer_km, 2)).toFixed(2)} km²
                </span>
              </div>
              
              <div className={`h-96 flex items-center justify-center ${
                theme === 'dark' ? 'bg-slate-800' : 'bg-gray-100'
              }`}>
                <div className="text-center">
                  <MapPin className="w-16 h-16 mx-auto mb-4 text-blue-500 opacity-50" />
                  <p className="text-sm text-slate-400">Interactive Map Component</p>
                  <p className="text-xs text-slate-500 mt-1">React-Leaflet integration here</p>
                </div>
              </div>
            </div>

            {/* AOI Controls */}
            <div className={`rounded-2xl p-6 shadow-xl ${
              theme === 'dark' ? 'bg-slate-900 border border-slate-800' : 'bg-white border border-gray-200'
            }`}>
              <h3 className="font-semibold mb-4">AOI Configuration</h3>
              
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={aoi.lon}
                    onChange={(e) => setAoi({...aoi, lon: parseFloat(e.target.value)})}
                    className={`w-full px-3 py-2 rounded-lg border ${
                      theme === 'dark' 
                        ? 'bg-slate-800 border-slate-700 focus:border-blue-500' 
                        : 'bg-white border-gray-300 focus:border-blue-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={aoi.lat}
                    onChange={(e) => setAoi({...aoi, lat: parseFloat(e.target.value)})}
                    className={`w-full px-3 py-2 rounded-lg border ${
                      theme === 'dark' 
                        ? 'bg-slate-800 border-slate-700 focus:border-blue-500' 
                        : 'bg-white border-gray-300 focus:border-blue-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-slate-400 mb-2">Buffer (km)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.6"
                    value={aoi.buffer_km}
                    onChange={(e) => setAoi({...aoi, buffer_km: parseFloat(e.target.value)})}
                    className={`w-full px-3 py-2 rounded-lg border ${
                      aoi.buffer_km < 0.6
                        ? 'border-red-500 bg-red-500/10'
                        : theme === 'dark' 
                          ? 'bg-slate-800 border-slate-700 focus:border-blue-500' 
                          : 'bg-white border-gray-300 focus:border-blue-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                  />
                </div>
              </div>
              
              {aoi.buffer_km < 0.6 && (
                <div className="mb-4 p-3 rounded-lg bg-orange-500/10 border border-orange-500/30 text-orange-400 text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  Buffer must be at least 0.6 km
                </div>
              )}

              <div className="flex gap-2">
                <button className="flex-1 px-2 py-1.5 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
                  Small (0.6km)
                </button>
                <button className="flex-1 px-2 py-1.5 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
                  Medium (1.5km)
                </button>
                <button className="flex-1 px-2 py-1.5 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
                  Large (3km)
                </button>
              </div>
            </div>

            {/* Pipeline Controls */}
            <div className={`rounded-2xl p-6 shadow-xl ${
              theme === 'dark' ? 'bg-slate-900 border border-slate-800' : 'bg-white border border-gray-200'
            }`}>
              <h3 className="font-semibold mb-4">Pipeline Controls</h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">Start Date</label>
                    <input
                      type="date"
                      defaultValue="2024-01-01"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        theme === 'dark' 
                          ? 'bg-slate-800 border-slate-700' 
                          : 'bg-white border-gray-300'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">End Date</label>
                    <input
                      type="date"
                      defaultValue="2024-12-31"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        theme === 'dark' 
                          ? 'bg-slate-800 border-slate-700' 
                          : 'bg-white border-gray-300'
                      } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm text-slate-400">Cloud Cover Max</label>
                    <span className="text-sm font-medium">30%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    defaultValue="30"
                    className="w-full accent-blue-500"
                  />
                </div>

                <button
                  onClick={runLandcover}
                  disabled={isRunning || aoi.buffer_km < 0.6}
                  className={cn(
                    'w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2',
                    isRunning || aoi.buffer_km < 0.6
                      ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white shadow-lg hover:shadow-xl'
                  )}
                >
                  {isRunning ? (
                    <>
                      <Activity className="w-5 h-5 animate-spin" />
                      Running Pipeline...
                    </>
                  ) : (
                    <>
                      <Satellite className="w-5 h-5" />
                      Run Landcover Pipeline
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Results & Status (40%) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Status Console */}
            <div className={`rounded-2xl overflow-hidden shadow-xl ${
              theme === 'dark' ? 'bg-slate-900 border border-slate-800' : 'bg-white border border-gray-200'
            }`}>
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-500" />
                  Pipeline Status
                </h3>
                <button 
                  onClick={() => setLogs([])}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  Clear
                </button>
              </div>
              
              <div className={`h-64 overflow-y-auto p-4 font-mono text-xs space-y-1 ${
                theme === 'dark' ? 'bg-slate-950' : 'bg-gray-50'
              }`}>
                {logs.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-slate-500">
                    <div className="text-center">
                      <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Waiting for pipeline execution...</p>
                    </div>
                  </div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-slate-500">[{log.time}]</span>
                      <span className={
                        log.message.includes('✓') ? 'text-green-400' :
                        log.message.includes('✅') ? 'text-emerald-400' :
                        log.message.includes('❌') ? 'text-red-400' :
                        'text-slate-300'
                      }>
                        {log.message}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Results Panel */}
            {results && (
              <div className={`rounded-2xl p-6 shadow-xl ${
                theme === 'dark' ? 'bg-slate-900 border border-slate-800' : 'bg-white border border-gray-200'
              }`}>
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <h3 className="font-semibold">Results</h3>
                </div>

                {/* Stats Table */}
                <div className="space-y-3 mb-6">
                  <h4 className="text-sm font-medium text-slate-400">Land Cover Statistics</h4>
                  {Object.entries(results.stats).map(([key, value]) => (
                    <div key={key} className={`p-3 rounded-lg ${
                      theme === 'dark' ? 'bg-slate-800' : 'bg-gray-50'
                    }`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium capitalize">{key}</span>
                        <span className="text-sm font-bold">{value.pct}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={cn(
                              'h-full transition-all',
                              key === 'water' ? 'bg-blue-500' : '',
                              key === 'trees' ? 'bg-green-600' : '',
                              key === 'grass' ? 'bg-green-400' : '',
                              key === 'crops' ? 'bg-yellow-500' : '',
                              key === 'built' ? 'bg-orange-500' : ''
                            )}
                            style={{ width: `${value.pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-400">{value.area.toFixed(2)} km²</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Download Files */}
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-3">Generated Files</h4>
                  <div className="space-y-2">
                    {results.files.map((file, i) => (
                      <button
                        key={i}
                        className={`w-full p-3 rounded-lg text-left flex items-center justify-between transition-colors ${
                          theme === 'dark' 
                            ? 'bg-slate-800 hover:bg-slate-700' 
                            : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-sm font-mono">{file}</span>
                        <Download className="w-4 h-4 text-blue-500" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}