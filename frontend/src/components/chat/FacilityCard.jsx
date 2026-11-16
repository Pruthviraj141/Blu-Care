import React from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Building2,
  Navigation,
  Phone,
  Clock,
  ExternalLink,
  MapPin,
  Star,
  ShieldCheck,
  Compass,
} from 'lucide-react';

/**
 * Robust parser to extract structured facility cards and Google Maps links
 * from markdown or plain text responses (e.g. historical chat messages).
 */
export const parseFacilitiesFromText = (text) => {
  if (!text || typeof text !== 'string') {
    return { facilities: [], externalSearch: {} };
  }

  const facilities = [];

  // Extract broader Google Maps search links
  let clinicsUrl = null;
  let hospitalsUrl = null;
  const clinicMatch = text.match(/\[(?:🔍\s*)?Search Nearby Clinics[^\]]*\]\((https:\/\/[^\s\)]+)\)/i);
  if (clinicMatch) clinicsUrl = clinicMatch[1];
  const hospitalMatch = text.match(/\[(?:🏥\s*)?Search Nearby Hospitals[^\]]*\]\((https:\/\/[^\s\)]+)\)/i);
  if (hospitalMatch) hospitalsUrl = hospitalMatch[1];

  // Also check generic google maps query URLs if not found
  if (!clinicsUrl) {
    const genericClinicMatch = text.match(/(https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=clinics[^\s\)]+)/i);
    if (genericClinicMatch) clinicsUrl = genericClinicMatch[1];
  }
  if (!hospitalsUrl) {
    const genericHospMatch = text.match(/(https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=hospitals[^\s\)]+)/i);
    if (genericHospMatch) hospitalsUrl = genericHospMatch[1];
  }

  // Regex to match facility items starting with "1. **NAME**" or "1. NAME"
  const itemRegex = /(?:^|\n|\s)(\d+)\.\s+\*\*([^*]+)\*\*([\s\S]*?)(?=(?:(?:\n|\s+)\d+\.\s+\*\*|\n\s*\*\*Explore|\s*\*\*Explore|\s*Map Data|\s*Distances are|\s*$))/g;

  let match;
  while ((match = itemRegex.exec(text)) !== null) {
    const rank = parseInt(match[1], 10);
    const rawName = match[2].trim();
    const details = match[3] || '';

    // Category: [Hospital], [Clinic], [Doctors], etc.
    const catMatch = details.match(/\[(Hospital|Clinic|Doctors|Doctor|Emergency|Health|Medical)[^\]]*\]/i);
    let category = catMatch ? catMatch[1].toLowerCase() : null;
    if (!category) {
      const lowerName = rawName.toLowerCase();
      if (lowerName.includes('hospital')) category = 'hospital';
      else if (lowerName.includes('clinic') || lowerName.includes('dispensary') || lowerName.includes('दवाखाना')) category = 'clinic';
      else category = 'doctors';
    }

    // Distance: (~178 m away ...) or (~1.2 km away)
    const distMatch = details.match(/\(~?([0-9.]+\s*(?:m|km|meters|miles))\s*away/i);
    const distance_formatted = distMatch ? distMatch[1].trim() : null;

    // Phone: 📞 099752 92424 or Phone: ...
    const phoneMatch = details.match(/(?:📞|phone[:\s]*)\s*([+0-9\s-]{7,22})/i);
    const phone = phoneMatch ? phoneMatch[1].trim() : null;

    // Address: - *Address*: JVGW+J85 or Address: ...
    const addrMatch = details.match(/(?:Address\*?:\s*|Address:\s*)([^\[\n\r]+)/i);
    const address = addrMatch ? addrMatch[1].replace(/^[-*\s]+|[-*\s]+$/g, '').trim() : null;

    // Directions: [🗺️ Directions](url) or [Directions](url)
    const dirMatch = details.match(/\[[^\]]*Directions\]\((https:\/\/[^\s\)]+)\)/i);
    const directions_url = dirMatch ? dirMatch[1] : null;

    // Extract coordinates if present in directions URL
    let latitude = null;
    let longitude = null;
    if (directions_url) {
      const coordMatch = directions_url.match(/destination=([0-9.-]+)(?:%2C|,)([0-9.-]+)/);
      if (coordMatch) {
        latitude = parseFloat(coordMatch[1]);
        longitude = parseFloat(coordMatch[2]);
      }
    }

    facilities.push({
      id: `parsed_fac_${rank}`,
      name: rawName,
      category,
      distance_formatted,
      phone,
      address,
      directions_url,
      maps_url: directions_url,
      latitude,
      longitude,
    });
  }

  return {
    facilities: facilities.slice(0, 5),
    externalSearch: {
      clinics_url: clinicsUrl,
      hospitals_url: hospitalsUrl,
      google_maps_clinics: clinicsUrl,
      google_maps_hospitals: hospitalsUrl,
    },
  };
};

export const SingleFacilityCard = ({ facility, rank = 1 }) => {
  if (!facility) return null;

  const {
    name = 'Healthcare Facility',
    category = 'hospital',
    specialty,
    rating,
    review_count,
    distance_formatted,
    distance_meters,
    address,
    phone,
    opening_hours,
    emergency,
  } = facility;

  const isFirst = rank === 1;
  const formattedDist =
    distance_formatted ||
    (distance_meters
      ? distance_meters < 1000
        ? `${Math.round(distance_meters)} m`
        : `${(distance_meters / 1000).toFixed(1)} km`
      : null);

  const getCategoryBadge = (cat) => {
    const c = (cat || '').toLowerCase();
    if (c.includes('hospital')) {
      return {
        label: 'Hospital',
        color: 'text-rose-300 bg-rose-500/15 border-rose-500/30',
      };
    }
    if (c.includes('clinic')) {
      return {
        label: 'Clinic',
        color: 'text-[var(--clinical-teal)] bg-[var(--clinical-teal)]/15 border-[var(--clinical-teal)]/30',
      };
    }
    return {
      label: 'Doctor / Practice',
      color: 'text-amber-300 bg-amber-500/15 border-amber-500/30',
    };
  };

  const badge = getCategoryBadge(category);

  const directionsUrl =
    facility.directions_url ||
    (facility.latitude && facility.longitude
      ? `https://www.google.com/maps/dir/?api=1&destination=${facility.latitude},${facility.longitude}`
      : facility.maps_url);

  const googleMapsUrl =
    facility.maps_url ||
    (facility.latitude && facility.longitude
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(name)}+${facility.latitude},${facility.longitude}`
      : null);

  return (
    <div
      className={`rounded-xl transition-all duration-200 relative overflow-hidden text-xs ${
        isFirst
          ? 'bg-gradient-to-br from-[var(--bg-surface)] via-[var(--bg-elevated)] to-[var(--bg-surface)] border-2 border-[var(--clinical-teal)] shadow-[0_0_24px_rgba(20,184,166,0.18)] p-4 sm:p-5'
          : 'bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] p-3.5 sm:p-4 shadow-sm'
      }`}
    >
      {/* Top Banner / Rank Indicator */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          {isFirst ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold tracking-wider uppercase bg-[var(--clinical-teal)] text-slate-950 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-950 animate-ping inline-block" />
              #1 Nearest Medical Facility
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wider bg-[var(--bg-elevated)] text-[var(--clinical-cyan)] border border-[var(--border-subtle)]">
              #{rank}
            </span>
          )}

          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border uppercase tracking-wider ${badge.color}`}>
            {badge.label}
          </span>

          {emergency === 'yes' && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              24/7 ER Casualty
            </span>
          )}
        </div>

        {/* Prominent Distance Display */}
        {formattedDist && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--clinical-teal)]/10 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] font-mono font-bold text-xs shrink-0">
            <Compass size={13} className="text-[var(--clinical-teal)] animate-spin-slow" />
            <span>~{formattedDist} away</span>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div className="space-y-1 min-w-0 flex-1">
            <h4
              className={`font-bold tracking-tight text-[var(--text-primary)] ${
                isFirst ? 'text-base sm:text-lg text-[var(--clinical-cyan)]' : 'text-sm sm:text-base'
              }`}
            >
              {name}
            </h4>

            {specialty && (
              <p className="text-[11px] font-medium text-[var(--clinical-teal)] flex items-center gap-1">
                <ShieldCheck size={12} />
                <span>Verified: {specialty}</span>
              </p>
            )}

            {rating != null && (
              <div className="flex items-center gap-1.5 text-[11px] pt-0.5">
                <div className="flex items-center text-amber-400 gap-0.5 font-bold">
                  <Star size={12} className="fill-amber-400 text-amber-400" />
                  <span>{rating.toFixed(1)}</span>
                </div>
                {review_count != null && (
                  <span className="text-[var(--text-muted)] font-mono text-[10px]">
                    ({review_count.toLocaleString()} patient reviews)
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-2 shrink-0 pt-1 sm:pt-0">
            {directionsUrl && (
              <a
                href={directionsUrl}
                target="_blank"
                rel="noreferrer"
                className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg font-bold text-xs transition-all shadow-sm focus-visible:outline-2 ${
                  isFirst
                    ? 'bg-[var(--clinical-teal)] text-slate-950 hover:opacity-95 ring-2 ring-[var(--clinical-teal)]/40 hover:scale-102'
                    : 'bg-[var(--clinical-teal)] text-slate-950 hover:opacity-90'
                }`}
                title="Open Turn-by-Turn GPS Navigation"
              >
                <Navigation size={13} className="fill-current" />
                <span>Directions</span>
              </a>
            )}

            {phone && (
              <a
                href={`tel:${phone}`}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[var(--bg-elevated)] hover:bg-[var(--bg-subtle)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--clinical-teal)] font-medium text-xs transition-colors"
                title={`Call ${name}`}
              >
                <Phone size={12} className="text-[var(--clinical-teal)]" />
                <span className="hidden sm:inline">Call</span>
              </a>
            )}

            {googleMapsUrl && (
              <a
                href={googleMapsUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-2 rounded-lg bg-[var(--bg-elevated)] hover:bg-[var(--bg-subtle)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] text-xs transition-colors"
                title="View Full Listing on Google Maps"
              >
                <ExternalLink size={12} />
              </a>
            )}
          </div>
        </div>

        {/* Address and Contact Information */}
        {address && (
          <div className="flex items-start gap-1.5 text-[11px] text-[var(--text-secondary)] pt-1">
            <MapPin size={13} className="text-[var(--text-muted)] shrink-0 mt-0.5" />
            <span className="leading-snug">{address}</span>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 pt-2 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)]">
          {phone && (
            <a
              href={`tel:${phone}`}
              className="inline-flex items-center gap-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <Phone size={11} className="text-[var(--clinical-teal)]" />
              <span className="font-mono">{phone}</span>
            </a>
          )}

          {opening_hours && (
            <div className="inline-flex items-center gap-1">
              <Clock size={11} />
              <span>{opening_hours}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const FacilityCardContainer = ({
  facilities = [],
  externalSearch = {},
  fallbackText = '',
}) => {
  // 1. Resolve structured list: if facilities is empty, parse from fallbackText
  let facilitiesList = Array.isArray(facilities) && facilities.length > 0 ? facilities : [];
  let mergedExternalSearch = { ...(externalSearch || {}) };

  if (facilitiesList.length === 0 && fallbackText) {
    const parsed = parseFacilitiesFromText(fallbackText);
    if (parsed.facilities && parsed.facilities.length > 0) {
      facilitiesList = parsed.facilities;
    }
    if (parsed.externalSearch) {
      if (parsed.externalSearch.clinics_url && !mergedExternalSearch.clinics_url && !mergedExternalSearch.google_maps_clinics) {
        mergedExternalSearch.google_maps_clinics = parsed.externalSearch.clinics_url;
      }
      if (parsed.externalSearch.hospitals_url && !mergedExternalSearch.hospitals_url && !mergedExternalSearch.google_maps_hospitals) {
        mergedExternalSearch.google_maps_hospitals = parsed.externalSearch.hospitals_url;
      }
    }
  }

  // 2. Strictly take top 5 facilities
  const topFive = facilitiesList.slice(0, 5);
  const hasFacilities = topFive.length > 0;

  const gmapsClinics =
    mergedExternalSearch?.google_maps_clinics ||
    mergedExternalSearch?.google_maps?.clinics_url ||
    mergedExternalSearch?.clinics_url ||
    'https://www.google.com/maps/search/?api=1&query=clinics+near+me';

  const gmapsHospitals =
    mergedExternalSearch?.google_maps_hospitals ||
    mergedExternalSearch?.google_maps?.hospitals_url ||
    mergedExternalSearch?.hospitals_url ||
    'https://www.google.com/maps/search/?api=1&query=hospitals+near+me';

  return (
    <div className="rounded-2xl bg-gradient-to-b from-[var(--bg-subtle)] to-[var(--bg-surface)] border border-[var(--border-strong)] p-4 sm:p-5 space-y-4 animate-fade-in text-xs max-w-2xl shadow-lg">
      {/* Container Header */}
      <div className="flex items-center justify-between gap-2 pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center shrink-0">
            <Building2 size={16} />
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text-primary)]">
              Top 5 Nearest Healthcare Facilities
            </h4>
            <p className="text-[11px] text-[var(--text-muted)]">
              Strictly verified & ranked nearest first by straight-line distance
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[var(--clinical-teal)]/15 text-[var(--clinical-teal)] font-bold border border-[var(--clinical-teal)]/30 shrink-0">
          {hasFacilities ? `Top ${topFive.length} Nearest` : 'Zero Within 5 km'}
        </span>
      </div>

      {/* Top 5 Facilities Stack in Ranked Cards */}
      {hasFacilities ? (
        <div className="space-y-3">
          {topFive.map((fac, idx) => (
            <SingleFacilityCard key={fac.id || idx} facility={fac} rank={idx + 1} />
          ))}
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2 text-[var(--text-secondary)]">
          <div className="prose prose-invert max-w-none text-xs leading-relaxed text-[var(--text-secondary)]">
            <ReactMarkdown>
              {fallbackText ||
                'No verified medical facilities were discovered within 5 km of your coordinates. You can explore broader Google Maps listings below.'}
            </ReactMarkdown>
          </div>
        </div>
      )}

      {/* External Local Search Actions */}
      <div className="space-y-2 pt-3 border-t border-[var(--border-subtle)]">
        <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider block">
          Broader Local Search on Google Maps
        </span>
        <div className="flex flex-wrap gap-2">
          {gmapsClinics && (
            <a
              href={gmapsClinics}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--clinical-teal)] font-medium text-xs transition-colors"
            >
              <span>Explore More Clinics on Google Maps</span>
              <ExternalLink size={12} />
            </a>
          )}

          {gmapsHospitals && (
            <a
              href={gmapsHospitals}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--clinical-cyan)] font-medium text-xs transition-colors"
            >
              <span>Explore More Hospitals on Google Maps</span>
              <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>

      <p className="text-[10px] text-[var(--text-muted)] italic pt-1">
        Distances are exact straight-line calculations. Tap Directions for live turn-by-turn routing with traffic.
      </p>
    </div>
  );
};

export default FacilityCardContainer;
