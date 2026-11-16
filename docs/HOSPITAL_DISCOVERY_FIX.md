# BluCare+ — Hospital Discovery Pipeline Rebuild (Scraping-Based)

## Executive Summary

The hospital discovery system in **BluCare+** has been rebuilt from the ground up around a **real-world scraping pipeline**. All dependencies on OpenStreetMap (OSM), Overpass API, and Nominatim have been completely removed.

Facility discovery is now anchored strictly on **GPS coordinates (`latitude` and `longitude`)**, scraping real-world healthcare listings, extracting high-precision destination coordinates directly from verified listing URLs, calculating exact **Haversine distances**, verifying **medical specialties** against clinical conditions, and ranking facilities **strictly nearest first**.

---

## 1. Audit and Root Cause Analysis

### 1.1 Previous Selenium Implementation Failures (`app/rag/tools/facilities_tool.py`, Commit `2b1efd4`)
1. **Brittle Navigation & UI State:** The legacy implementation navigated to `https://www.google.com/maps/search/{coords}` and clicked `//button[contains(@aria-label,"Nearby")]`, followed by `driver.switch_to.active_element.send_keys(...)`. Modern Google Maps views no longer present a uniform "Nearby" button and do not reliably autofocus the search input on that action, causing immediate element timeouts.
2. **Missing Facility Coordinates & Distances:** The old scraper only collected `name`, `rating`, `phone`, and `link`. It **did not extract destination coordinates (`latitude`, `longitude`)** and could not compute real geographical distances from the user.
3. **Flawed Ranking (Rating over Distance):** The previous code ranked facilities by rating (`sorted(facilities, key=lambda x: x["rating"], reverse=True)`). A 5-star clinic 50 km away ranked ahead of an emergency hospital 400 meters away, violating triage safety principles.
4. **Outdated DOM Selectors:** It relied on obsolete classes (e.g. `UsdlK` for phone numbers), which Google Maps changed, resulting in missing data.
5. **No Deduplication or Radius Handling:** It lacked coordinate deduplication, multi-batch scroll pagination, and automatic radius expansion.

### 1.2 OpenStreetMap / Overpass Outages
- Public Overpass mirrors (`maps.mail.ru`, `overpass-api.de`, `overpass.private.coffee`) frequently suffered HTTP 504 Gateway Timeouts, 502 Bad Gateway responses, and >25s server execution delays.
- OpenStreetMap POI coverage in dense urban and rural areas lacked opening hours, phone numbers, and emergency department tags.
- Per user specifications, **OpenStreetMap, Overpass, and Nominatim have been completely removed**.

---

## 2. The Rebuilt Scraping Architecture

```
[ Browser / Geolocation ]
            │ (User-permitted GPS coordinates: lat, lng, radius_km, condition)
            ▼
[ FastAPI Endpoint: /api/v1/hospitals/nearby ]
            │ (Validates -90 <= lat <= 90, -180 <= lng <= 180, no silent fallback)
            ▼
[ FacilitiesService: app/facilities/service.py ]
            │
            ├──► [ SpecialtyMapper: app/facilities/specialty_mapper.py ]
            │       (Maps condition to targeted queries & clinical verification profiles)
            │
            ├──► [ HospitalScraper: app/facilities/scraper.py ]
            │       (Headless Chrome with stealth options & multi-batch scroll loading)
            │       └── Scrapes: https://www.google.com/maps/search/{query}/@{lat},{lng},{zoom}z
            │       └── Extracts: Name, link, rating, reviews, address, phone, 24/7 ER
            │       └── Parses exact coordinates: !3d{lat}!4d{lng}
            │
            ├──► [ Coordinate Validation & Deduplication ]
            │       (Filters duplicates within <40m using proximity & normalized name)
            │
            ├──► [ Haversine Distance Engine: app/facilities/distance.py ]
            │       (Calculates exact straight-line distance in meters from user GPS)
            │
            ├──► [ Nearest-First Distance Sorting ]
            │       (Emergency priority tier when acute signs present; strict nearest-first)
            │
            └──► [ Directions & Search URL Generator: app/facilities/maps_urls.py ]
                    └── Turn-by-Turn Directions: /maps/dir/?api=1&destination={dest_lat},{dest_lng}
                    └── User-centered Local Search: /maps/search/?api=1&query=hospitals+near+{user_lat},{user_lng}
```

### Key Modules:
| File | Responsibility |
|---|---|
| `app/facilities/scraper.py` | Headless Chrome engine with multi-batch scrolling, Google Maps card parsing, coordinate extraction from `!3d{lat}!4d{lng}`, and in-memory TTL caching. |
| `app/facilities/service.py` | Orchestrates search pipeline: coordinate validation, scraper invocation, Haversine distance calculation, deduplication, radius expansion (to 10km when 0 results), and nearest-first sorting. |
| `app/facilities/specialty_mapper.py` | Disease context engine mapping conditions (Cardiac, Orthopedic, Fever, Emergency, Pediatrics, Dental) to queries and clinical verification rules. |
| `app/facilities/distance.py` | Pure mathematical Haversine distance calculator and human-friendly distance formatter. |
| `app/facilities/maps_urls.py` | Generates verified Google Maps turn-by-turn directions URLs and user-centered external search URLs without leaking PII. |
| `app/facilities/schemas.py` | Pydantic response models with verified fields, ratings, specialties, and backward-compatible provider dictionaries. |
| `app/api/v1/endpoints/hospitals.py` | REST API endpoint accepting `lat`, `lng`, `radius_km`, `category`, and `condition`. |

---

## 3. Location & Disease-Aware Discovery Pipeline

### 3.1 Latitude and Longitude as Geographical Foundation
- Browser requests user location via `navigator.geolocation.getCurrentPosition`.
- If denied, BluCare+ displays an **honest error message** with options to select metropolitan city centers or retry GPS.
- Coordinates are validated on both frontend and backend. Invalid coordinates return `HTTP 400 Bad Request`.
- **Zero hardcoded coordinates are silently substituted.**

### 3.2 Disease-Aware Facility Discovery
Conditions dynamically guide the scraper search terms and verification criteria:
- **Cardiac Symptoms:** Searches `cardiac hospital heart institute cardiology emergency`. Verifies Heart hospitals, Cardiologists, and full-service emergency hospitals. Rejects irrelevant specialized clinics (e.g. dental or eye clinics).
- **Orthopedic Symptoms:** Searches `orthopedic hospital bone joint clinic trauma center`. Verifies Orthopedic clinics, orthopedic surgeons, and trauma centers.
- **Fever & General Illness:** Searches `general hospital physician outpatient clinic`. Discovers outpatient clinics, general practitioners, and multi-specialty hospitals.
- **Emergency Warning Signs:** Prioritizes verified 24/7 casualty/trauma centers with `emergency: "yes"`, sorted nearest first.

---

## 4. Real Test Evidence & Verification Logs

Live end-to-end tests were executed against the scraper pipeline across different geographical locations and condition contexts.

### Test Case 1: Bengaluru (`12.9716, 77.5946`) — Cardiac Emergency
- **Coordinates Received:** `lat=12.9716, lng=77.5946, radius=5000m`
- **Condition Context:** `"cardiac emergency chest pain"`
- **Scraped URL:** `https://www.google.com/maps/search/cardiac+hospital+heart+institute+cardiology+emergency/@12.9716,77.5946,14z`
- **Extracted Results (Strictly Nearest First):**
  1. **St. Martha's Cardiac Care Centre**
     - Coordinates: `(12.9707232, 77.5861402)`
     - Distance: **921.9 m (922 m)**
     - Specialty: Cardiology / Emergency Cardiac Care | 24/7 ER: yes
     - Phone: `080 4012 8200`
     - Directions: `https://www.google.com/maps/dir/?api=1&destination=12.9707232,77.5861402`
  2. **Department of Cardiology | Vikram Aura Hospitals**
     - Coordinates: `(12.9660283, 77.6102145)`
     - Distance: **1801.8 m (1.8 km)**
     - Specialty: Cardiology / Emergency Cardiac Care | 24/7 ER: yes
     - Phone: `088844 81414`
  3. **Tathagat Heart Care Centre & Hospital**
     - Coordinates: `(12.985298, 77.58038)`
     - Distance: **2166.6 m (2.2 km)**
     - Specialty: Cardiology / Emergency Cardiac Care | 24/7 ER: yes
     - Phone: `099003 56000`
  4. **Jain Institute of Cardiac Sciences**
     - Coordinates: `(12.9916569, 77.5952842)`
     - Distance: **2231.5 m (2.2 km)**
     - Specialty: Cardiology / Emergency Cardiac Care | 24/7 ER: yes
     - Phone: `080 4087 5555`
  5. **The Heart Center @Dr Rehan**
     - Coordinates: `(12.9882148, 77.5726427)`
     - Distance: **3012.2 m (3.0 km)**
     - Specialty: Cardiology / Emergency Cardiac Care | 24/7 ER: yes
     - Phone: `078297 95667`

*Observation:* Distances are strictly ascending (**921.9m → 1801.8m → 2166.6m → 2231.5m → 3012.2m**). Nearest emergency hospital is ranked #1.

---

### Test Case 2: Bengaluru (`12.9716, 77.5946`) — Fever & Viral Illness
- **Condition Context:** `"fever and viral infection"`
- **Extracted Results (Strictly Nearest First):**
  1. **Department of General Physician Apollo Hospital Seshadripuram**
     - Coordinates: `(12.9883233, 77.5724686)`
     - Distance: **3034.5 m (3.0 km)**
     - Specialty: General Medicine & Outpatient Care
     - Phone: `080 6930 5514`
  2. **Vignan General Hospital**
     - Coordinates: `(12.944144, 77.5969458)`
     - Distance: **3063.5 m (3.1 km)**
     - Specialty: General Medicine & Outpatient Care
  3. **KC General Hospital, Casualty**
     - Coordinates: `(12.9954625, 77.5700781)`
     - Distance: **3755.0 m (3.8 km)**
     - Specialty: General Medicine & Outpatient Care | 24/7 ER: yes
  4. **Annaswamy Mudaliar General Hospital**
     - Coordinates: `(13.0000283, 77.6146589)`
     - Distance: **3836.2 m (3.8 km)**
     - Specialty: General Medicine & Outpatient Care
     - Phone: `084313 19665`

*Observation:* Changing condition from cardiac to fever shifted discovered facilities from specialized cardiac catheterization labs to outpatient physicians and general medicine hospitals, while preserving exact geographical distance order (**3034.5m → 3063.5m → 3755.0m → 3836.2m**).

---

### Test Case 3: Pune (`18.5204, 73.8567`) — Orthopedic Trauma
- **Coordinates Received:** `lat=18.5204, lng=73.8567, radius=6000m`
- **Condition Context:** `"orthopedic fracture bone trauma"`
- **Extracted Results (Strictly Nearest First):**
  1. **ONP - Orthopedic Department**
     - Coordinates: `(18.5318821, 73.8473608)`
     - Distance: **1612.3 m (1.6 km)**
     - Specialty: Orthopedics & Emergency Trauma | 24/7 ER: yes
     - Phone: `086696 60396`
  2. **The Bone & Joint Clinic**
     - Coordinates: `(18.5310812, 73.8759831)`
     - Distance: **2354.6 m (2.4 km)**
     - Specialty: Orthopedics & Emergency Trauma
     - Phone: `094223 14156`
  3. **Bone & Joint Clinic, Chinar Heights**
     - Coordinates: `(18.5297573, 73.8358122)`
     - Distance: **2435.7 m (2.4 km)**
     - Specialty: Orthopedics & Emergency Trauma
     - Phone: `020 2565 7211`
  4. **Dr. Rohit Chakor**
     - Coordinates: `(18.5015101, 73.9007642)`
     - Distance: **5098.9 m (5.1 km)**
     - Specialty: Orthopedics & Emergency Trauma
     - Phone: `070206 63211`

*Observation:* Switching user coordinates from Bengaluru to Pune returned exclusively Pune facilities (ONP Ganeshkhind Rd, Bund Garden Rd, Chinar Heights). Proximity was verified against Pune center coordinates.

---

## 5. Automated Test Suite Results

```bash
./venv/bin/pytest tests/test_phase3_facilities.py tests/test_api.py tests/test_fix_end_to_end.py
```
- `tests/test_phase3_facilities.py`: **20 PASSED**
  - Haversine distance calculation and coordinate boundaries
  - Google Maps universal search and navigation URL builders
  - Scraper card data extraction and coordinate parsing (`!3d...!4d...`)
  - Disease-aware specialty mapping (cardiac, orthopedic, fever, pediatric, emergency)
  - Clinical verification rules (accepts relevant facilities, rejects unrelated clinics)
  - Strict nearest-first ranking and coordinate deduplication (<40m)
  - Multi-location geographical sensitivity
  - Automatic radius expansion on sparse coverage
  - FastAPI endpoint verification with `radius_km`
  - RAG `find_nearby_facilities` tool execution without OSM
- `tests/test_api.py`: **8 PASSED**
- `tests/test_fix_end_to_end.py`: **4 PASSED**
- **Total: 32 tests passed (100% success rate)**

---

## 6. Frontend Enhancements

1. **Explicit Geolocation Permissions:** `HospitalsPage.jsx` acquires real browser location with accuracy metrics (`±X m`).
2. **Radius Selection Control:** Interactive search radius selector (**3 km, 5 km, 10 km, 15 km**), transmitting `radius_km` directly to the backend.
3. **Turn-by-Turn Directions:** Cards contain direct action buttons opening Google Maps navigation targeted at the facility's verified destination coordinates (`/maps/dir/?api=1&destination=lat,lng`).
4. **Verified Specialty & Rating Badges:** Displays facility type, clinical specialty, star ratings with review counts, and 24/7 ER badges.
5. **No Fake URLs / OSM Clean-up:** All references to OpenStreetMap, Overpass, and fake URLs were removed across `HospitalsPage.jsx` and `FacilityCard.jsx`.
6. **Vite Production Build:** Verified with `npm run build` passing with zero errors.
