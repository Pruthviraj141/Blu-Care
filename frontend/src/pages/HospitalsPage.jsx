// src/pages/HospitalsPage.jsx - Top 5 Nearest Hospitals & Healthcare Facilities Discovery
import React, { useState, useEffect } from 'react';
import PageContainer from '../components/ui/PageContainer';
import SectionHeader from '../components/ui/SectionHeader';
import { SingleFacilityCard } from '../components/chat/FacilityCard';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '@clerk/clerk-react';
import { hospitalsApi } from '../utils/api';
import { logger } from '../utils/logger';
import {
  PhoneCall,
  MapPin,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Building2,
  ExternalLink,
  Navigation,
  Compass,
  SlidersHorizontal,
  ShieldCheck,
  Award,
} from 'lucide-react';

const PRESET_CITIES = [
  { name: 'Bengaluru', latitude: 12.9716, longitude: 77.5946 },
  { name: 'Mumbai', latitude: 19.0760, longitude: 72.8777 },
  { name: 'Delhi NCR', latitude: 28.6139, longitude: 77.2090 },
  { name: 'Pune', latitude: 18.5204, longitude: 73.8567 },
  { name: 'Hyderabad', latitude: 17.3850, longitude: 78.4867 },
  { name: 'London', latitude: 51.5074, longitude: -0.1278 },
];

const CONDITION_PRESETS = [
  { label: 'All Healthcare', value: '' },
  { label: 'General / Fever / Clinic', value: 'fever and general clinic' },
  { label: 'Cardiac & Chest Pain', value: 'cardiac emergency chest pain' },
  { label: 'Orthopedic & Fracture', value: 'orthopedic trauma fracture' },
  { label: 'Pediatric & Children', value: 'pediatric child clinic' },
  { label: 'Dental Care', value: 'dental clinic' },
];

const RADIUS_OPTIONS = [
  { label: 'Within 5 km (Strictly Nearest)', value: 5 },
  { label: 'Within 10 km', value: 10 },
  { label: 'Within 15 km', value: 15 },
];

const HospitalsPage = () => {
  const { addToast } = useToast();
  const { getToken } = useAuth();

  const [locationState, setLocationState] = useState('requesting'); // requesting | granted | denied | manual
  const [errorMessage, setErrorMessage] = useState('');
  const [coords, setCoords] = useState(null);
  const [selectedCityName, setSelectedCityName] = useState(null);
  const [conditionFilter, setConditionFilter] = useState('');
  const [radiusKm, setRadiusKm] = useState(5); // Default: strictly 5km
  const [accuracy, setAccuracy] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const [isSearching, setIsSearching] = useState(false);
  const [facilities, setFacilities] = useState([]);
  const [externalSearch, setExternalSearch] = useState({});
  const [activeCategory, setActiveCategory] = useState('all'); // 'all' | 'hospital' | 'clinic'

  // Fetch facilities on coordinates change, condition change, or radius change
  const fetchFacilities = async (lat, lng, cond = conditionFilter, rKm = radiusKm) => {
    if (lat == null || lng == null) return;
    setIsSearching(true);
    try {
      // Strictly request top 5 facilities from backend
      const data = await hospitalsApi.getNearbyFacilities(lat, lng, 'all', cond || null, rKm, { getToken });
      if (data) {
        if (Array.isArray(data.facilities)) {
          // Strictly enforce top 5 nearest
          setFacilities(data.facilities.slice(0, 5));
        } else {
          setFacilities([]);
        }
        if (data.external_search) {
          setExternalSearch(data.external_search);
        }
      }
    } catch (err) {
      logger.error('Failed to load facilities:', err);
      addToast('Unable to connect to live facilities service. Google Maps search available.', 'warning');
    } finally {
      setIsSearching(false);
    }
  };

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationState('denied');
      setErrorMessage('Geolocation is unsupported by your browser. Please select a city below.');
      return;
    }

    setLocationState('requesting');
    setErrorMessage('');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy: acc } = position.coords;
        const newCoords = { latitude, longitude };
        setCoords(newCoords);
        setSelectedCityName(null);
        setAccuracy(Math.round(acc));
        setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
        setLocationState('granted');
        addToast('Exact GPS coordinates acquired', 'success');
        fetchFacilities(latitude, longitude, conditionFilter, radiusKm);
      },
      (error) => {
        setLocationState('denied');
        setErrorMessage(
          error.code === 1
            ? 'Browser location access was denied. Please select a city below or enable GPS permissions to locate real nearby facilities.'
            : 'Device location timed out or is unavailable. Please select a city below.'
        );
        addToast('Location access not granted. Select your city to discover local facilities.', 'info');
      },
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 60000,
      }
    );
  };

  const handleSelectCity = (city) => {
    const newCoords = { latitude: city.latitude, longitude: city.longitude };
    setCoords(newCoords);
    setSelectedCityName(city.name);
    setLocationState('manual');
    setAccuracy(null);
    setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    fetchFacilities(city.latitude, city.longitude, conditionFilter, radiusKm);
  };

  const handleConditionChange = (newCond) => {
    setConditionFilter(newCond);
    if (coords?.latitude != null && coords?.longitude != null) {
      fetchFacilities(coords.latitude, coords.longitude, newCond, radiusKm);
    }
  };

  const handleRadiusChange = (newRadius) => {
    setRadiusKm(newRadius);
    if (coords?.latitude != null && coords?.longitude != null) {
      fetchFacilities(coords.latitude, coords.longitude, conditionFilter, newRadius);
    }
  };

  // Initial load
  useEffect(() => {
    requestLocation();
  }, []);

  // Filter facilities and ensure strictly top 5
  const hospitalList = facilities.filter((f) => (f.category || '').toLowerCase().includes('hospital'));
  const clinicList = facilities.filter(
    (f) => (f.category || '').toLowerCase().includes('clinic') || (f.category || '').toLowerCase().includes('doctor')
  );

  const displayedFacilities = (
    activeCategory === 'hospital' ? hospitalList : activeCategory === 'clinic' ? clinicList : facilities
  ).slice(0, 5);

  // External Google Maps URLs
  const latStr = coords?.latitude != null ? coords.latitude : '';
  const lngStr = coords?.longitude != null ? coords.longitude : '';
  const gmapsHospitalsUrl =
    externalSearch?.google_maps_hospitals ||
    externalSearch?.google_maps?.hospitals_url ||
    (latStr ? `https://www.google.com/maps/search/?api=1&query=hospitals+near+${latStr},${lngStr}` : 'https://www.google.com/maps/search/?api=1&query=hospitals+near+me');

  const gmapsClinicsUrl =
    externalSearch?.google_maps_clinics ||
    externalSearch?.google_maps?.clinics_url ||
    (latStr ? `https://www.google.com/maps/search/?api=1&query=clinics+near+${latStr},${lngStr}` : 'https://www.google.com/maps/search/?api=1&query=clinics+near+me');

  const gmapsEmergencyUrl = latStr
    ? `https://www.google.com/maps/search/?api=1&query=emergency+room+hospital+near+${latStr},${lngStr}`
    : 'https://www.google.com/maps/search/?api=1&query=emergency+room+hospital+near+me';

  return (
    <PageContainer>
      {/* Hero Section */}
      <SectionHeader
        title="Top 5 Nearest Hospitals &"
        highlightTitle="Healthcare Facilities"
        description="Verified medical centers strictly ordered nearest-first based on your exact coordinates within 5 km."
        tag="Scraper-Verified Nearest Care"
      />

      <div className="space-y-6 max-w-4xl mx-auto pb-24">
        {/* Permission Denied Notice with City Selectors */}
        {locationState === 'denied' && (
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 space-y-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-amber-400 shrink-0 mt-0.5" size={20} />
              <div>
                <h4 className="text-sm font-bold text-amber-300">Device Location Access Needed</h4>
                <p className="text-xs text-amber-200/80 mt-0.5">
                  {errorMessage || 'Browser geolocation was not provided. Please choose a city below or enable GPS permissions to locate real nearby facilities.'}
                </p>
              </div>
            </div>
            <div className="pt-2 border-t border-amber-500/20">
              <span className="text-xs font-semibold text-amber-300 block mb-2">Or select your metropolitan area:</span>
              <div className="flex flex-wrap gap-2">
                {PRESET_CITIES.map((city) => (
                  <button
                    key={city.name}
                    type="button"
                    onClick={() => handleSelectCity(city)}
                    className="px-3 py-1.5 rounded-lg text-xs bg-[var(--bg-surface)] border border-amber-500/30 hover:border-amber-400 text-amber-100 hover:bg-amber-500/20 transition-colors cursor-pointer"
                  >
                    📍 {city.name}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={requestLocation}
                  className="px-3 py-1.5 rounded-[6px] text-xs bg-[var(--accent-primary)] text-[#101316] font-medium hover:bg-[var(--accent-hover)] transition-colors cursor-pointer ml-auto"
                >
                  Enable GPS Location
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Location Status Bar */}
        <div className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center shrink-0">
              <MapPin size={20} />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                  {locationState === 'granted'
                    ? 'Device GPS Locked'
                    : locationState === 'manual'
                    ? `City Center: ${selectedCityName}`
                    : 'Location Status'}
                </span>
                {accuracy && (
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-mono flex items-center gap-1 font-semibold">
                    <CheckCircle2 size={10} /> ±{accuracy}m accuracy
                  </span>
                )}
                {locationState === 'manual' && (
                  <span className="text-[10px] text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded-full font-mono font-semibold">
                    Manual City Selection
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-[var(--text-secondary)] mt-0.5 truncate">
                {coords
                  ? `Coordinates: ${coords.latitude.toFixed(4)}° N, ${coords.longitude.toFixed(4)}° E`
                  : 'Acquiring location permission...'}
                {lastUpdated && ` · Updated: ${lastUpdated}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={requestLocation}
              disabled={locationState === 'requesting'}
              className="px-3.5 py-2 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] text-xs text-[var(--text-primary)] hover:bg-[var(--bg-subtle)] transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50 shrink-0 font-medium"
            >
              <RefreshCw size={13} className={locationState === 'requesting' ? 'animate-spin' : ''} />
              <span>{locationState === 'requesting' ? 'Locating...' : 'Refresh GPS'}</span>
            </button>
          </div>
        </div>

        {/* Condition Filter & Radius Selector Controls */}
        <div className="space-y-3">
          {/* Condition-Aware Specialty Filter Pills */}
          <div className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider block">
                Filter by Medical Need / Specialty:
              </span>
              <span className="text-[11px] text-[var(--clinical-teal)] font-medium">
                Targeted Clinical Queries
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {CONDITION_PRESETS.map((cond) => {
                const isSelected = conditionFilter === cond.value;
                return (
                  <button
                    key={cond.label}
                    type="button"
                    onClick={() => handleConditionChange(cond.value)}
                    className={`px-3 py-1.5 rounded-[6px] text-xs font-medium transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--accent-primary)] text-[#101316] font-semibold shadow-sm'
                        : 'bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)]'
                    }`}
                  >
                    {cond.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Search Radius Selection */}
          <div className="p-3.5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={14} className="text-[var(--clinical-teal)]" />
              <span className="text-xs font-bold text-[var(--text-primary)]">Search Distance:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {RADIUS_OPTIONS.map((opt) => {
                const isSelected = radiusKm === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleRadiusChange(opt.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--accent-primary)] text-[#101316] font-semibold shadow-sm'
                        : 'bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)]'
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Category Tabs: All, Hospitals Only, Clinics Only */}
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveCategory('all')}
              className={`px-3 py-1.5 rounded-[6px] text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === 'all'
                  ? 'bg-[var(--accent-primary)] text-[#101316]'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
              }`}
            >
              Top 5 Nearest ({displayedFacilities.length})
            </button>

            <button
              type="button"
              onClick={() => setActiveCategory('hospital')}
              className={`px-3 py-1.5 rounded-[6px] text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === 'hospital'
                  ? 'bg-[var(--severity-emergency)] text-white'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
              }`}
            >
              Hospitals ({hospitalList.length})
            </button>

            <button
              type="button"
              onClick={() => setActiveCategory('clinic')}
              className={`px-3 py-1.5 rounded-[6px] text-xs font-semibold transition-colors cursor-pointer ${
                activeCategory === 'clinic'
                  ? 'bg-[var(--accent-hover)] text-[#101316]'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
              }`}
            >
              Clinics ({clinicList.length})
            </button>
          </div>

          <span className="text-[11px] font-mono text-[var(--text-muted)] hidden sm:inline">
            Ranked 1 to 5 by shortest straight-line distance
          </span>
        </div>

        {/* Loading Spinner */}
        {isSearching && (
          <div className="p-12 text-center space-y-3 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-sm">
            <Loader2 size={36} className="mx-auto text-[var(--clinical-teal)] animate-spin" />
            <p className="text-sm text-[var(--text-primary)] font-bold">Scanning top 5 nearest facilities within {radiusKm} km...</p>
            <p className="text-xs text-[var(--text-muted)]">Extracting real hospital coordinates, specialties, and turn-by-turn directions</p>
          </div>
        )}

        {/* TOP 5 ORDERED FACILITIES LIST */}
        {!isSearching && (
          <div className="space-y-3.5">
            {displayedFacilities.length > 0 ? (
              displayedFacilities.map((fac, idx) => (
                <SingleFacilityCard key={fac.id || idx} facility={fac} rank={idx + 1} />
              ))
            ) : (
              <div className="p-10 text-center space-y-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-sm">
                <Building2 size={40} className="mx-auto text-[var(--text-muted)] opacity-60" />
                <div className="space-y-1.5 max-w-md mx-auto">
                  <h4 className="text-sm font-bold text-[var(--text-primary)]">
                    No verified healthcare facilities found within {radiusKm} km
                  </h4>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    Local clinics in your immediate area may not be indexed under this specialty. You can expand the search radius to 10 km or explore direct Google Maps live search.
                  </p>
                </div>
                <div className="pt-2 flex flex-wrap justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => handleRadiusChange(10)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--clinical-teal)] font-bold text-xs hover:border-[var(--clinical-teal)] transition-colors cursor-pointer"
                  >
                    <span>Expand to 10 km Radius</span>
                  </button>
                  <a
                    href={gmapsHospitalsUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-[6px] bg-[var(--accent-primary)] text-[#101316] font-semibold text-xs hover:bg-[var(--accent-hover)] transition-colors"
                  >
                    <span>Explore on Google Maps</span>
                    <ExternalLink size={13} />
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Quick Google Maps External Actions Bar */}
        <div className="p-4 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-strong)] space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-1.5">
              <Compass size={14} className="text-[var(--clinical-teal)]" />
              <span>Broader Google Maps Local Search</span>
            </span>
            <span className="text-[11px] text-[var(--text-muted)] font-mono">Centered on User GPS</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <a
              href={gmapsHospitalsUrl}
              target="_blank"
              rel="noreferrer"
              className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-rose-500/40 text-rose-300 hover:bg-rose-500/10 transition-all flex items-center justify-between group cursor-pointer shadow-sm"
            >
              <div className="flex items-center gap-2">
                <Building2 size={16} className="text-rose-400 group-hover:scale-110 transition-transform" />
                <span className="text-xs font-medium text-[var(--text-primary)]">Hospitals Near Me</span>
              </div>
              <ExternalLink size={13} className="text-rose-400 opacity-70 group-hover:opacity-100 transition-opacity" />
            </a>

            <a
              href={gmapsClinicsUrl}
              target="_blank"
              rel="noreferrer"
              className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--clinical-teal)]/40 text-[var(--clinical-teal)] hover:bg-[var(--clinical-teal)]/10 transition-all flex items-center justify-between group cursor-pointer shadow-sm"
            >
              <div className="flex items-center gap-2">
                <Building2 size={16} className="text-[var(--clinical-teal)] group-hover:scale-110 transition-transform" />
                <span className="text-xs font-medium text-[var(--text-primary)]">Clinics Near Me</span>
              </div>
              <ExternalLink size={13} className="text-[var(--clinical-teal)] opacity-70 group-hover:opacity-100 transition-opacity" />
            </a>

            <a
              href={gmapsEmergencyUrl}
              target="_blank"
              rel="noreferrer"
              className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-amber-500/40 text-amber-300 hover:bg-amber-500/10 transition-all flex items-center justify-between group cursor-pointer shadow-sm"
            >
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-400 group-hover:scale-110 transition-transform" />
                <span className="text-xs font-medium text-[var(--text-primary)]">24/7 Casualty / ER</span>
              </div>
              <ExternalLink size={13} className="text-amber-400 opacity-70 group-hover:opacity-100 transition-opacity" />
            </a>
          </div>
        </div>
      </div>

      {/* Floating Persistent Call 108 Emergency SOS Button */}
      <div className="fixed bottom-20 md:bottom-6 right-4 md:right-6 z-50">
        <a
          href="tel:108"
          className="no-underline flex items-center gap-2 px-4 py-2.5 rounded-[8px] bg-[var(--severity-emergency)] hover:brightness-110 text-white font-semibold text-xs shadow-lg transition-all transform hover:scale-105 active:scale-95"
          title="Direct Emergency Hotline"
        >
          <PhoneCall size={15} className="animate-pulse" />
          <span>Emergency SOS 108</span>
        </a>
      </div>
    </PageContainer>
  );
};

export default HospitalsPage;
