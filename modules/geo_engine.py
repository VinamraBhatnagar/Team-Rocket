"""
Geo Engine Module
Geospatial crime data processing, CSV upload handling, and India location mapping.
"""

import os
import io
import re
import math
import pandas as pd
from collections import defaultdict

# ── India State Centroid Coordinates ──────────────────────────────
INDIA_STATE_COORDS = {
    'Andhra Pradesh': (15.9129, 79.7400),
    'Arunachal Pradesh': (28.2180, 94.7278),
    'Assam': (26.2006, 92.9376),
    'Bihar': (25.0961, 85.3131),
    'Chhattisgarh': (21.2787, 81.8661),
    'Goa': (15.2993, 74.1240),
    'Gujarat': (22.2587, 71.1924),
    'Haryana': (29.0588, 76.0856),
    'Himachal Pradesh': (31.1048, 77.1734),
    'Jharkhand': (23.6102, 85.2799),
    'Karnataka': (15.3173, 75.7139),
    'Kerala': (10.8505, 76.2711),
    'Madhya Pradesh': (22.9734, 78.6569),
    'Maharashtra': (19.7515, 75.7139),
    'Manipur': (24.6637, 93.9063),
    'Meghalaya': (25.4670, 91.3662),
    'Mizoram': (23.1645, 92.9376),
    'Nagaland': (26.1584, 94.5624),
    'Odisha': (20.9517, 85.0985),
    'Punjab': (31.1471, 75.3412),
    'Rajasthan': (27.0238, 74.2179),
    'Sikkim': (27.5330, 88.5122),
    'Tamil Nadu': (11.1271, 78.6569),
    'Telangana': (18.1124, 79.0193),
    'Tripura': (23.9408, 91.9882),
    'Uttar Pradesh': (26.8467, 80.9462),
    'Uttarakhand': (30.0668, 79.0193),
    'West Bengal': (22.9868, 87.8550),
    'Delhi': (28.7041, 77.1025),
    'Jammu & Kashmir': (33.7782, 76.5762),
    'Ladakh': (34.1526, 77.5771),
    'Chandigarh': (30.7333, 76.7794),
    'Puducherry': (11.9416, 79.8083),
    'Andaman & Nicobar': (11.7401, 92.6586),
    'Dadra and Nagar Haveli and Daman and Diu': (20.1809, 73.0169),
    'Lakshadweep': (10.5667, 72.6417),
}

# ── City to State Mapping ─────────────────────────────────────────
CITY_TO_STATE = {
    # Maharashtra
    'mumbai': 'Maharashtra', 'pune': 'Maharashtra', 'nagpur': 'Maharashtra',
    'nashik': 'Maharashtra', 'thane': 'Maharashtra', 'aurangabad': 'Maharashtra',
    'navi mumbai': 'Maharashtra', 'solapur': 'Maharashtra', 'kolhapur': 'Maharashtra',
    # Delhi
    'delhi': 'Delhi', 'new delhi': 'Delhi',
    # Karnataka
    'bangalore': 'Karnataka', 'bengaluru': 'Karnataka', 'mysore': 'Karnataka',
    'mysuru': 'Karnataka', 'mangalore': 'Karnataka', 'mangaluru': 'Karnataka',
    'hubli': 'Karnataka', 'belgaum': 'Karnataka',
    # Tamil Nadu
    'chennai': 'Tamil Nadu', 'coimbatore': 'Tamil Nadu', 'madurai': 'Tamil Nadu',
    'salem': 'Tamil Nadu', 'trichy': 'Tamil Nadu', 'tiruchirappalli': 'Tamil Nadu',
    'tirunelveli': 'Tamil Nadu', 'erode': 'Tamil Nadu', 'vellore': 'Tamil Nadu',
    # Telangana
    'hyderabad': 'Telangana', 'warangal': 'Telangana', 'nizamabad': 'Telangana',
    'secunderabad': 'Telangana',
    # West Bengal
    'kolkata': 'West Bengal', 'howrah': 'West Bengal', 'durgapur': 'West Bengal',
    'siliguri': 'West Bengal', 'asansol': 'West Bengal',
    # Gujarat
    'ahmedabad': 'Gujarat', 'surat': 'Gujarat', 'vadodara': 'Gujarat',
    'rajkot': 'Gujarat', 'gandhinagar': 'Gujarat', 'bhavnagar': 'Gujarat',
    # Rajasthan
    'jaipur': 'Rajasthan', 'jodhpur': 'Rajasthan', 'udaipur': 'Rajasthan',
    'kota': 'Rajasthan', 'ajmer': 'Rajasthan', 'bikaner': 'Rajasthan',
    # Uttar Pradesh
    'lucknow': 'Uttar Pradesh', 'agra': 'Uttar Pradesh', 'varanasi': 'Uttar Pradesh',
    'kanpur': 'Uttar Pradesh', 'mathura': 'Uttar Pradesh', 'noida': 'Uttar Pradesh',
    'ghaziabad': 'Uttar Pradesh', 'meerut': 'Uttar Pradesh', 'allahabad': 'Uttar Pradesh',
    'prayagraj': 'Uttar Pradesh', 'bareilly': 'Uttar Pradesh', 'aligarh': 'Uttar Pradesh',
    'moradabad': 'Uttar Pradesh', 'gorakhpur': 'Uttar Pradesh',
    # Madhya Pradesh
    'bhopal': 'Madhya Pradesh', 'indore': 'Madhya Pradesh', 'gwalior': 'Madhya Pradesh',
    'jabalpur': 'Madhya Pradesh', 'ujjain': 'Madhya Pradesh',
    # Bihar
    'patna': 'Bihar', 'gaya': 'Bihar', 'muzaffarpur': 'Bihar', 'bhagalpur': 'Bihar',
    # Odisha
    'bhubaneswar': 'Odisha', 'cuttack': 'Odisha', 'rourkela': 'Odisha',
    # Punjab
    'chandigarh': 'Chandigarh', 'amritsar': 'Punjab', 'ludhiana': 'Punjab',
    'jalandhar': 'Punjab', 'patiala': 'Punjab', 'bathinda': 'Punjab',
    # Haryana
    'gurgaon': 'Haryana', 'gurugram': 'Haryana', 'faridabad': 'Haryana',
    'karnal': 'Haryana', 'panipat': 'Haryana', 'rohtak': 'Haryana',
    # Kerala
    'thiruvananthapuram': 'Kerala', 'kochi': 'Kerala', 'kozhikode': 'Kerala',
    'thrissur': 'Kerala', 'ernakulam': 'Kerala', 'calicut': 'Kerala',
    # Assam
    'guwahati': 'Assam', 'dibrugarh': 'Assam', 'silchar': 'Assam',
    # Jharkhand
    'ranchi': 'Jharkhand', 'jamshedpur': 'Jharkhand', 'dhanbad': 'Jharkhand',
    'bokaro': 'Jharkhand',
    # Chhattisgarh
    'raipur': 'Chhattisgarh', 'bilaspur': 'Chhattisgarh', 'durg': 'Chhattisgarh',
    # Uttarakhand
    'dehradun': 'Uttarakhand', 'haridwar': 'Uttarakhand', 'rishikesh': 'Uttarakhand',
    'nainital': 'Uttarakhand',
    # Goa
    'panaji': 'Goa', 'margao': 'Goa', 'vasco': 'Goa',
    # J&K
    'srinagar': 'Jammu & Kashmir', 'jammu': 'Jammu & Kashmir',
    # NE States
    'imphal': 'Manipur', 'shillong': 'Meghalaya', 'aizawl': 'Mizoram',
    'kohima': 'Nagaland', 'gangtok': 'Sikkim', 'agartala': 'Tripura',
    'itanagar': 'Arunachal Pradesh',
    # Andhra Pradesh
    'visakhapatnam': 'Andhra Pradesh', 'vizag': 'Andhra Pradesh',
    'vijayawada': 'Andhra Pradesh', 'tirupati': 'Andhra Pradesh',
    'guntur': 'Andhra Pradesh', 'nellore': 'Andhra Pradesh',
    'amaravati': 'Andhra Pradesh',
}

# ── City Coordinates ──────────────────────────────────────────────
CITY_COORDS = {
    'mumbai': (19.0760, 72.8777), 'pune': (18.5204, 73.8567),
    'nagpur': (21.1458, 79.0882), 'delhi': (28.6139, 77.2090),
    'new delhi': (28.6139, 77.2090), 'bangalore': (12.9716, 77.5946),
    'bengaluru': (12.9716, 77.5946), 'chennai': (13.0827, 80.2707),
    'hyderabad': (17.3850, 78.4867), 'kolkata': (22.5726, 88.3639),
    'ahmedabad': (23.0225, 72.5714), 'jaipur': (26.9124, 75.7873),
    'lucknow': (26.8467, 80.9462), 'bhopal': (23.2599, 77.4126),
    'patna': (25.6093, 85.1376), 'bhubaneswar': (20.2961, 85.8245),
    'thiruvananthapuram': (8.5241, 76.9366), 'kochi': (9.9312, 76.2673),
    'guwahati': (26.1445, 91.7362), 'ranchi': (23.3441, 85.3096),
    'raipur': (21.2514, 81.6296), 'dehradun': (30.3165, 78.0322),
    'chandigarh': (30.7333, 76.7794), 'surat': (21.1702, 72.8311),
    'vadodara': (22.3072, 73.1812), 'indore': (22.7196, 75.8577),
    'coimbatore': (11.0168, 76.9558), 'visakhapatnam': (17.6868, 83.2185),
    'agra': (27.1767, 78.0081), 'varanasi': (25.3176, 82.9739),
    'kanpur': (26.4499, 80.3319), 'mathura': (27.4924, 77.6737),
    'noida': (28.5355, 77.3910), 'ghaziabad': (28.6692, 77.4538),
    'meerut': (28.9845, 77.7064), 'gurgaon': (28.4595, 77.0266),
    'gurugram': (28.4595, 77.0266), 'faridabad': (28.4089, 77.3178),
    'amritsar': (31.6340, 74.8723), 'ludhiana': (30.9010, 75.8573),
    'jodhpur': (26.2389, 73.0243), 'udaipur': (24.5854, 73.7125),
    'kota': (25.2138, 75.8648), 'mysore': (12.2958, 76.6394),
    'mangalore': (12.9141, 74.8560), 'madurai': (9.9252, 78.1198),
    'salem': (11.6643, 78.1460), 'srinagar': (34.0837, 74.7973),
    'jammu': (32.7266, 74.8570), 'panaji': (15.4909, 73.8278),
    'gangtok': (27.3389, 88.6065), 'imphal': (24.8170, 93.9368),
    'shillong': (25.5788, 91.8933), 'aizawl': (23.7271, 92.7176),
    'kohima': (25.6751, 94.1086), 'agartala': (23.8315, 91.2868),
    'itanagar': (27.0844, 93.6053), 'shimla': (31.1048, 77.1734),
    'jamshedpur': (22.8046, 86.2029), 'dhanbad': (23.7957, 86.4304),
    'gwalior': (26.2183, 78.1828), 'jabalpur': (23.1815, 79.9864),
    'vijayawada': (16.5062, 80.6480), 'warangal': (17.9784, 79.5941),
    'cuttack': (20.4625, 85.8830), 'nashik': (20.0063, 73.7900),
    'thane': (19.2183, 72.9781),
}

# ── Normalisation for GeoJSON ST_NM matching ─────────────────────
# The GeoJSON uses 'ST_NM' with specific spelling; map common variants
STATE_NAME_NORMALIZE = {
    'andaman and nicobar': 'Andaman & Nicobar',
    'andaman and nicobar islands': 'Andaman & Nicobar',
    'andaman & nicobar islands': 'Andaman & Nicobar',
    'andaman & nicobar': 'Andaman & Nicobar',
    'andhra pradesh': 'Andhra Pradesh',
    'arunachal pradesh': 'Arunachal Pradesh',
    'assam': 'Assam',
    'bihar': 'Bihar',
    'chandigarh': 'Chandigarh',
    'chhattisgarh': 'Chhattisgarh',
    'chattisgarh': 'Chhattisgarh',
    'dadra and nagar haveli and daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'dadra & nagar haveli': 'Dadra and Nagar Haveli and Daman and Diu',
    'daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'daman & diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'delhi': 'Delhi',
    'nct of delhi': 'Delhi',
    'new delhi': 'Delhi',
    'goa': 'Goa',
    'gujarat': 'Gujarat',
    'haryana': 'Haryana',
    'himachal pradesh': 'Himachal Pradesh',
    'jammu and kashmir': 'Jammu & Kashmir',
    'jammu & kashmir': 'Jammu & Kashmir',
    'j&k': 'Jammu & Kashmir',
    'jharkhand': 'Jharkhand',
    'karnataka': 'Karnataka',
    'kerala': 'Kerala',
    'ladakh': 'Ladakh',
    'lakshadweep': 'Lakshadweep',
    'madhya pradesh': 'Madhya Pradesh',
    'maharashtra': 'Maharashtra',
    'manipur': 'Manipur',
    'meghalaya': 'Meghalaya',
    'mizoram': 'Mizoram',
    'nagaland': 'Nagaland',
    'odisha': 'Odisha',
    'orissa': 'Odisha',
    'puducherry': 'Puducherry',
    'pondicherry': 'Puducherry',
    'punjab': 'Punjab',
    'rajasthan': 'Rajasthan',
    'sikkim': 'Sikkim',
    'tamil nadu': 'Tamil Nadu',
    'tamilnadu': 'Tamil Nadu',
    'telangana': 'Telangana',
    'tripura': 'Tripura',
    'uttar pradesh': 'Uttar Pradesh',
    'up': 'Uttar Pradesh',
    'uttarakhand': 'Uttarakhand',
    'uttaranchal': 'Uttarakhand',
    'west bengal': 'West Bengal',
}

# ── Column Detection Patterns ─────────────────────────────────────
COLUMN_PATTERNS = {
    'state': ['state', 'province', 'region', 'stnm', 'statename', 'statecode'],
    'city': ['city', 'town', 'municipality', 'cityname'],
    'district': ['district', 'dist', 'districtname'],
    'area': ['area', 'locality', 'location', 'place', 'address', 'zone'],
    'latitude': ['latitude', 'lat'],
    'longitude': ['longitude', 'lng', 'lon', 'long'],
    'crime_type': ['crime', 'crimetype', 'offense', 'offence', 'category',
                   'type', 'crimeCategory', 'primarytype', 'crimecategory'],
    'count': ['count', 'crimecount', 'cases', 'total', 'totalcrimes',
              'incidents', 'frequency', 'number', 'noofcases', 'numberofcrimes'],
    'date': ['date', 'year', 'crimedate', 'incidentdate', 'reportdate',
             'dateofreport', 'dateofcrime', 'incidentyear', 'crimeyear'],
}

# Max upload limits
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_ROW_COUNT = 1_000_000


class GeoEngine:
    """Geospatial crime data processing engine."""

    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.uploaded_data = None  # Stores processed uploaded CSV geodata
        self.uploaded_raw = None   # Stores the raw processed DataFrame
        self.uploaded_stats = None
        self.uploaded_filters = None

    # ── Existing dataset ──────────────────────────────────────────

    def get_existing_crime_geodata(self, crime_type=None, year=None, location_query=None):
        """
        Aggregate crime data from the project's incidents.csv.
        Returns state-level and city-level aggregations with coordinates.
        """
        incidents = self.data_processor.incidents
        if not incidents:
            return {'geodata': [], 'stats': {}, 'filters': {}, 'state_data': {}}

        # Build working list
        records = []
        for inc in incidents:
            loc_str = str(inc.get('location', ''))
            parsed = self._parse_location(loc_str)
            state = parsed.get('state')
            city = parsed.get('city')

            if not state and not city:
                continue

            rec = {
                'state': state or 'Unknown',
                'city': city or '',
                'location_raw': loc_str,
                'crime_type': str(inc.get('crime_type', 'UNKNOWN')),
                'date': str(inc.get('date', '')),
                'year': str(inc.get('date', ''))[:4] if inc.get('date') else '',
            }
            records.append(rec)

        if not records:
            return {'geodata': [], 'stats': {}, 'filters': {}, 'state_data': {}}

        df = pd.DataFrame(records)

        # Gather filters before filtering
        all_crime_types = sorted(df['crime_type'].dropna().unique().tolist())
        all_years = sorted(df['year'].dropna().unique().tolist())
        all_years = [y for y in all_years if y and len(y) == 4]

        # Apply filters
        if crime_type and crime_type != 'All':
            df = df[df['crime_type'] == crime_type]
        if year and year != 'All':
            df = df[df['year'] == str(year)]
        if location_query:
            q = location_query.lower()
            df = df[
                df['state'].str.lower().str.contains(q, na=False) |
                df['city'].str.lower().str.contains(q, na=False) |
                df['location_raw'].str.lower().str.contains(q, na=False)
            ]

        # State-level aggregation
        state_agg = df.groupby('state').agg(
            crime_count=('state', 'size'),
        ).reset_index()

        state_data = {}
        for _, row in state_agg.iterrows():
            state_name = row['state']
            normalized = self._normalize_state_name(state_name)
            coords = INDIA_STATE_COORDS.get(normalized, (0, 0))
            state_crimes = df[df['state'] == state_name]
            crime_breakdown = state_crimes['crime_type'].value_counts().to_dict()

            state_data[normalized] = {
                'state': normalized,
                'crime_count': int(row['crime_count']),
                'lat': coords[0],
                'lng': coords[1],
                'crime_types': crime_breakdown,
            }

        # City-level aggregation
        geodata = []
        city_agg = df.groupby(['state', 'city']).agg(
            crime_count=('city', 'size'),
        ).reset_index()

        for _, row in city_agg.iterrows():
            city = row['city'].lower().strip() if row['city'] else ''
            state = row['state']
            coords = CITY_COORDS.get(city, None)
            if not coords:
                normalized_state = self._normalize_state_name(state)
                coords = INDIA_STATE_COORDS.get(normalized_state, (0, 0))

            city_crimes = df[(df['state'] == state) & (df['city'] == row['city'])]
            crime_breakdown = city_crimes['crime_type'].value_counts().to_dict()

            geodata.append({
                'location': row['city'] if row['city'] else state,
                'state': state,
                'city': row['city'],
                'crime_count': int(row['crime_count']),
                'lat': coords[0],
                'lng': coords[1],
                'crime_types': crime_breakdown,
            })

        # Stats
        stats = self._compute_stats(df)

        return {
            'geodata': geodata,
            'state_data': state_data,
            'stats': stats,
            'filters': {
                'crime_types': all_crime_types,
                'years': all_years,
            },
        }

    # ── CSV Upload Processing ─────────────────────────────────────

    def process_uploaded_csv(self, file_content, filename, file_size):
        """
        Process an uploaded CSV file.
        Returns preview info, validation results, geodata, and statistics.
        """
        errors = []
        warnings = []

        # 1. Validate file type
        if not filename.lower().endswith('.csv'):
            return {'status': 'error', 'message': 'Invalid file type. Please upload a .csv file.'}

        # 2. Validate file size
        if file_size > MAX_FILE_SIZE_BYTES:
            return {'status': 'error',
                    'message': f'File too large ({file_size / 1024 / 1024:.1f} MB). Maximum allowed: 50 MB.'}

        # 3. Try to read CSV
        try:
            df = pd.read_csv(io.StringIO(file_content), encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.StringIO(file_content), encoding='latin-1')
            except Exception as e:
                return {'status': 'error', 'message': f'Unable to read CSV file: {str(e)}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Unable to parse CSV file: {str(e)}'}

        # 4. Validate not empty
        if df.empty:
            return {'status': 'error', 'message': 'The CSV file is empty. No data rows found.'}

        if len(df) > MAX_ROW_COUNT:
            return {'status': 'error',
                    'message': f'CSV has {len(df):,} rows. Maximum allowed: {MAX_ROW_COUNT:,}. '
                               f'Please reduce the dataset size.'}

        # 5. Detect columns
        detected = self._detect_columns(df)

        # 6. Validate geographic columns exist
        has_geo = bool(detected.get('state') or detected.get('city') or
                       detected.get('district') or detected.get('area'))
        has_coords = bool(detected.get('latitude') and detected.get('longitude'))

        if not has_geo and not has_coords:
            return {
                'status': 'error',
                'message': 'Unable to map this dataset. Missing geographic information. '
                           'Please provide State, City, District, or Latitude/Longitude columns.',
                'columns_found': list(df.columns),
            }

        # 7. Determine CSV structure and process
        has_count = bool(detected.get('count'))
        has_crime_type = bool(detected.get('crime_type'))

        # Validate numeric columns
        if has_count:
            count_col = detected['count']
            df[count_col] = pd.to_numeric(df[count_col], errors='coerce')
            invalid_count = df[count_col].isna().sum()
            if invalid_count > 0:
                warnings.append(f'{invalid_count} rows have non-numeric crime count values (set to 0).')
                df[count_col] = df[count_col].fillna(0)

        if has_coords:
            lat_col = detected['latitude']
            lng_col = detected['longitude']
            df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
            df[lng_col] = pd.to_numeric(df[lng_col], errors='coerce')

            # Validate coordinate ranges
            invalid_coords = (
                (df[lat_col] < -90) | (df[lat_col] > 90) |
                (df[lng_col] < -180) | (df[lng_col] > 180)
            ).sum()
            if invalid_coords > 0:
                warnings.append(f'{invalid_coords} rows have invalid lat/lng values.')

            null_coords = df[lat_col].isna().sum() + df[lng_col].isna().sum()
            if null_coords > 0:
                warnings.append(f'{null_coords} rows have missing lat/lng values.')

        # Check for duplicates
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            warnings.append(f'{dup_count} duplicate rows detected.')

        # Check for missing values in key columns
        for col_type, col_name in detected.items():
            if col_name:
                null_count = df[col_name].isna().sum()
                if null_count > 0:
                    warnings.append(f'{null_count} missing values in "{col_name}" column.')

        # 8. Detect date column
        detected_date = detected.get('date')
        years = []
        if detected_date:
            try:
                date_series = pd.to_datetime(df[detected_date], errors='coerce')
                df['_parsed_year'] = date_series.dt.year.astype('Int64').astype(str)
                years = sorted(df['_parsed_year'].dropna().unique().tolist())
                years = [y for y in years if y != '<NA>' and y != 'nan']
            except Exception:
                # Maybe it's already a year column
                if df[detected_date].dtype in ['int64', 'float64']:
                    df['_parsed_year'] = df[detected_date].astype('Int64').astype(str)
                    years = sorted(df['_parsed_year'].dropna().unique().tolist())
                    years = [y for y in years if y != '<NA>' and y != 'nan']

        # 9. Process geodata
        geodata, state_data, unmatched = self._process_csv_geodata(df, detected, has_count, has_coords)

        # 10. Compute statistics
        if has_count:
            total_crimes = int(df[detected['count']].sum())
        else:
            total_crimes = len(df)

        crime_types = []
        if has_crime_type:
            crime_types = sorted(df[detected['crime_type']].dropna().unique().tolist())

        stats = {
            'total_crimes': total_crimes,
            'states_affected': len(state_data),
            'cities_districts': len(geodata),
            'most_common_crime': '',
            'highest_crime_location': '',
        }

        if has_crime_type:
            if has_count:
                crime_agg = df.groupby(detected['crime_type'])[detected['count']].sum()
                if not crime_agg.empty:
                    stats['most_common_crime'] = str(crime_agg.idxmax())
            else:
                top_crime = df[detected['crime_type']].mode()
                if not top_crime.empty:
                    stats['most_common_crime'] = str(top_crime.iloc[0])

        if state_data:
            max_state = max(state_data.values(), key=lambda x: x['crime_count'])
            stats['highest_crime_location'] = max_state['state']

        # 11. Build preview
        preview_rows = df.head(10).fillna('').to_dict('records')
        # Sanitize values for display
        for row in preview_rows:
            for key in row:
                row[key] = str(row[key])[:200]  # Truncate long values

        detected_display = {}
        for col_type, col_name in detected.items():
            if col_name:
                detected_display[col_type] = col_name

        result = {
            'status': 'success',
            'filename': filename,
            'preview': {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'detected_columns': detected_display,
                'first_rows': preview_rows,
            },
            'stats': stats,
            'geodata': geodata,
            'state_data': state_data,
            'unmatched': unmatched[:100],  # Limit unmatched to 100
            'unmatched_count': len(unmatched),
            'mapped_count': len(df) - len(unmatched),
            'filters': {
                'crime_types': crime_types,
                'years': years,
            },
            'warnings': warnings,
            'errors': errors,
        }

        # Store for later use
        self.uploaded_data = result
        self.uploaded_raw = df
        self.uploaded_stats = stats
        self.uploaded_filters = {
            'crime_types': crime_types,
            'years': years,
            'detected': detected,
            'has_count': has_count,
            'has_coords': has_coords,
        }

        return result

    def get_uploaded_filtered(self, crime_type=None, year=None, location_query=None):
        """Re-aggregate uploaded data with new filters."""
        if self.uploaded_raw is None or self.uploaded_filters is None:
            return None

        df = self.uploaded_raw.copy()
        detected = self.uploaded_filters['detected']
        has_count = self.uploaded_filters['has_count']
        has_coords = self.uploaded_filters['has_coords']

        # Apply crime type filter
        if crime_type and crime_type != 'All' and detected.get('crime_type'):
            df = df[df[detected['crime_type']] == crime_type]

        # Apply year filter
        if year and year != 'All' and '_parsed_year' in df.columns:
            df = df[df['_parsed_year'] == str(year)]

        # Apply location filter
        if location_query:
            q = location_query.lower()
            mask = pd.Series([False] * len(df), index=df.index)
            for col_type in ['state', 'city', 'district', 'area']:
                col = detected.get(col_type)
                if col:
                    mask = mask | df[col].astype(str).str.lower().str.contains(q, na=False)
            df = df[mask]

        geodata, state_data, unmatched = self._process_csv_geodata(df, detected, has_count, has_coords)

        # Recompute stats for filtered data
        if has_count and detected.get('count'):
            total_crimes = int(df[detected['count']].sum())
        else:
            total_crimes = len(df)

        stats = {
            'total_crimes': total_crimes,
            'states_affected': len(state_data),
            'cities_districts': len(geodata),
            'most_common_crime': '',
            'highest_crime_location': '',
        }

        if detected.get('crime_type'):
            if has_count and detected.get('count'):
                crime_agg = df.groupby(detected['crime_type'])[detected['count']].sum()
                if not crime_agg.empty:
                    stats['most_common_crime'] = str(crime_agg.idxmax())
            else:
                top_crime = df[detected['crime_type']].mode()
                if not top_crime.empty:
                    stats['most_common_crime'] = str(top_crime.iloc[0])

        if state_data:
            max_state = max(state_data.values(), key=lambda x: x['crime_count'])
            stats['highest_crime_location'] = max_state['state']

        return {
            'geodata': geodata,
            'state_data': state_data,
            'stats': stats,
            'unmatched_count': len(unmatched),
            'mapped_count': len(df) - len(unmatched),
        }

    # ── Internal helpers ──────────────────────────────────────────

    def _detect_columns(self, df):
        """
        Intelligently detect column roles using fuzzy name matching.
        Returns dict mapping role → column name (or None).
        Two-pass approach: exact match first, then prefix/contains match.
        """
        detected = {key: None for key in COLUMN_PATTERNS}
        columns = list(df.columns)
        used_columns = set()

        # Pass 1: Exact match (highest confidence)
        for col in columns:
            normalized = self._normalize_col_name(col)
            for role, patterns in COLUMN_PATTERNS.items():
                if detected[role] is not None:
                    continue
                for pattern in patterns:
                    if normalized == pattern:
                        detected[role] = col
                        used_columns.add(col)
                        break

        # Pass 2: Prefix / endswith match (lower confidence, skip already used)
        for col in columns:
            if col in used_columns:
                continue
            normalized = self._normalize_col_name(col)
            for role, patterns in COLUMN_PATTERNS.items():
                if detected[role] is not None:
                    continue
                for pattern in patterns:
                    if len(pattern) >= 3 and (normalized.startswith(pattern) or normalized.endswith(pattern)):
                        detected[role] = col
                        used_columns.add(col)
                        break

        return detected

    def _normalize_col_name(self, name):
        """Normalize a column name for matching: lowercase, remove spaces/underscores/hyphens."""
        return re.sub(r'[\s_\-]+', '', str(name).lower().strip())

    def _normalize_state_name(self, name):
        """Normalize a state name to match GeoJSON ST_NM values."""
        if not name:
            return ''
        key = name.lower().strip()
        return STATE_NAME_NORMALIZE.get(key, name)

    def _parse_location(self, location_str):
        """
        Parse a location string like 'Marine Drive, Mumbai' or 'Sector 15, New Delhi'.
        Returns dict with 'state' and 'city' keys.
        """
        if not location_str or location_str == 'nan':
            return {'state': None, 'city': None}

        result = {'state': None, 'city': None}

        # Check if the whole string matches a state
        norm = location_str.lower().strip()
        if norm in STATE_NAME_NORMALIZE:
            result['state'] = STATE_NAME_NORMALIZE[norm]
            return result

        # Check if the whole string matches a city
        if norm in CITY_TO_STATE:
            result['city'] = location_str.strip()
            result['state'] = CITY_TO_STATE[norm]
            return result

        # Try splitting by comma - typically "Area, City" format
        parts = [p.strip() for p in location_str.split(',')]
        for part in reversed(parts):  # Check from right (city usually last)
            p_lower = part.lower().strip()
            if p_lower in CITY_TO_STATE:
                result['city'] = part.strip()
                result['state'] = CITY_TO_STATE[p_lower]
                return result
            if p_lower in STATE_NAME_NORMALIZE:
                result['state'] = STATE_NAME_NORMALIZE[p_lower]
                return result

        # Try matching any known city name within the string
        for city, state in CITY_TO_STATE.items():
            if city in norm:
                result['city'] = city.title()
                result['state'] = state
                return result

        return result

    def _geocode_location(self, state=None, city=None, district=None, area=None):
        """Get coordinates for a location using the built-in lookup tables."""
        # Try city first (more precise)
        if city:
            city_lower = city.lower().strip()
            if city_lower in CITY_COORDS:
                return CITY_COORDS[city_lower]
            # Try to find state from city
            if city_lower in CITY_TO_STATE:
                state = CITY_TO_STATE[city_lower]

        # Try district (often same as city in India)
        if district:
            dist_lower = district.lower().strip()
            if dist_lower in CITY_COORDS:
                return CITY_COORDS[dist_lower]
            if dist_lower in CITY_TO_STATE:
                state = CITY_TO_STATE[dist_lower]

        # Fall back to state centroid
        if state:
            normalized = self._normalize_state_name(state)
            if normalized in INDIA_STATE_COORDS:
                return INDIA_STATE_COORDS[normalized]

        return None

    def _process_csv_geodata(self, df, detected, has_count, has_coords):
        """Process CSV DataFrame into geodata format."""
        geodata = []
        state_data = {}
        unmatched = []

        if has_coords and detected.get('latitude') and detected.get('longitude'):
            # Structure C: Lat/Lng data
            geodata, state_data, unmatched = self._process_coords_data(df, detected, has_count)
        else:
            # Structure A or B: Location-based data
            geodata, state_data, unmatched = self._process_location_data(df, detected, has_count)

        return geodata, state_data, unmatched

    def _process_location_data(self, df, detected, has_count):
        """Process location-based CSV data (Structure A or B)."""
        geodata = []
        state_data = defaultdict(lambda: {'crime_count': 0, 'crime_types': defaultdict(int)})
        unmatched = []

        state_col = detected.get('state')
        city_col = detected.get('city')
        district_col = detected.get('district')
        area_col = detected.get('area')
        crime_col = detected.get('crime_type')
        count_col = detected.get('count')

        # Determine grouping columns
        group_cols = []
        if state_col:
            group_cols.append(state_col)
        if city_col:
            group_cols.append(city_col)
        if district_col:
            group_cols.append(district_col)

        if not group_cols:
            if area_col:
                group_cols.append(area_col)

        if not group_cols:
            return geodata, {}, unmatched

        # Aggregate
        if has_count and count_col:
            agg_df = df.groupby(group_cols, dropna=False).agg(
                crime_count=(count_col, 'sum')
            ).reset_index()
        else:
            agg_df = df.groupby(group_cols, dropna=False).size().reset_index(name='crime_count')

        # Also get crime type breakdown per group
        for _, row in agg_df.iterrows():
            state_val = str(row.get(state_col, '')) if state_col else ''
            city_val = str(row.get(city_col, '')) if city_col else ''
            dist_val = str(row.get(district_col, '')) if district_col else ''

            # Determine state
            state_name = ''
            if state_val and state_val != 'nan':
                state_name = self._normalize_state_name(state_val)
            elif city_val and city_val.lower().strip() in CITY_TO_STATE:
                state_name = CITY_TO_STATE[city_val.lower().strip()]
            elif dist_val and dist_val.lower().strip() in CITY_TO_STATE:
                state_name = CITY_TO_STATE[dist_val.lower().strip()]

            if not state_name:
                unmatched.append({
                    'location': f"{state_val} / {city_val} / {dist_val}".strip(' /'),
                    'reason': 'Could not determine state',
                    'crime_count': int(row['crime_count']),
                })
                continue

            # Get coordinates
            coords = self._geocode_location(
                state=state_name,
                city=city_val if city_val != 'nan' else None,
                district=dist_val if dist_val != 'nan' else None,
            )
            if not coords:
                unmatched.append({
                    'location': f"{state_val} / {city_val} / {dist_val}".strip(' /'),
                    'reason': 'Could not geocode location',
                    'crime_count': int(row['crime_count']),
                })
                continue

            # Get crime type breakdown
            mask = pd.Series([True] * len(df), index=df.index)
            for gc in group_cols:
                mask = mask & (df[gc] == row[gc])
            subset = df[mask]
            crime_breakdown = {}
            if crime_col:
                if has_count and count_col:
                    crime_breakdown = subset.groupby(crime_col)[count_col].sum().to_dict()
                else:
                    crime_breakdown = subset[crime_col].value_counts().to_dict()

            location_label = city_val if city_val and city_val != 'nan' else (
                dist_val if dist_val and dist_val != 'nan' else state_name
            )

            geodata.append({
                'location': location_label,
                'state': state_name,
                'city': city_val if city_val != 'nan' else '',
                'district': dist_val if dist_val != 'nan' else '',
                'crime_count': int(row['crime_count']),
                'lat': coords[0],
                'lng': coords[1],
                'crime_types': {str(k): int(v) for k, v in crime_breakdown.items()},
            })

            # State aggregation
            state_data[state_name]['crime_count'] += int(row['crime_count'])
            for ct, cv in crime_breakdown.items():
                state_data[state_name]['crime_types'][str(ct)] += int(cv)

        # Finalize state_data
        final_state_data = {}
        for state_name, data in state_data.items():
            coords = INDIA_STATE_COORDS.get(state_name, (0, 0))
            final_state_data[state_name] = {
                'state': state_name,
                'crime_count': data['crime_count'],
                'lat': coords[0],
                'lng': coords[1],
                'crime_types': dict(data['crime_types']),
            }

        return geodata, final_state_data, unmatched

    def _process_coords_data(self, df, detected, has_count):
        """Process coordinate-based CSV data (Structure C)."""
        geodata = []
        state_data = defaultdict(lambda: {'crime_count': 0, 'crime_types': defaultdict(int)})
        unmatched = []

        lat_col = detected['latitude']
        lng_col = detected['longitude']
        crime_col = detected.get('crime_type')
        count_col = detected.get('count')
        state_col = detected.get('state')
        city_col = detected.get('city')

        for idx, row in df.iterrows():
            lat = row.get(lat_col)
            lng = row.get(lng_col)

            if pd.isna(lat) or pd.isna(lng):
                continue

            try:
                lat = float(lat)
                lng = float(lng)
            except (ValueError, TypeError):
                continue

            if lat < -90 or lat > 90 or lng < -180 or lng > 180:
                continue

            crime_type = str(row.get(crime_col, 'Unknown')) if crime_col else 'Unknown'
            crime_count = int(row.get(count_col, 1)) if has_count and count_col else 1
            state = str(row.get(state_col, '')) if state_col else ''
            city = str(row.get(city_col, '')) if city_col else ''

            if not state or state == 'nan':
                state = self._reverse_geocode_state(lat, lng)

            state_name = self._normalize_state_name(state) if state else 'Unknown'

            geodata.append({
                'location': city if city and city != 'nan' else state_name,
                'state': state_name,
                'city': city if city != 'nan' else '',
                'crime_count': crime_count,
                'lat': lat,
                'lng': lng,
                'crime_types': {crime_type: crime_count} if crime_type != 'nan' else {},
            })

            state_data[state_name]['crime_count'] += crime_count
            if crime_type and crime_type != 'nan':
                state_data[state_name]['crime_types'][crime_type] += crime_count

        # Finalize state_data
        final_state_data = {}
        for state_name, data in state_data.items():
            coords = INDIA_STATE_COORDS.get(state_name, (0, 0))
            final_state_data[state_name] = {
                'state': state_name,
                'crime_count': data['crime_count'],
                'lat': coords[0],
                'lng': coords[1],
                'crime_types': dict(data['crime_types']),
            }

        return geodata, final_state_data, unmatched

    def _reverse_geocode_state(self, lat, lng):
        """Simple reverse geocoding: find the closest state centroid."""
        min_dist = float('inf')
        closest = 'Unknown'
        for state, (s_lat, s_lng) in INDIA_STATE_COORDS.items():
            dist = math.sqrt((lat - s_lat) ** 2 + (lng - s_lng) ** 2)
            if dist < min_dist:
                min_dist = dist
                closest = state
        return closest

    def _compute_stats(self, df):
        """Compute dashboard statistics from a DataFrame."""
        total_crimes = len(df)
        states_affected = df['state'].nunique()
        cities = df['city'].nunique() if 'city' in df.columns else 0
        most_common_crime = ''
        if 'crime_type' in df.columns:
            mode = df['crime_type'].mode()
            if not mode.empty:
                most_common_crime = str(mode.iloc[0])

        highest_crime_location = ''
        if 'state' in df.columns:
            top_state = df['state'].value_counts()
            if not top_state.empty:
                highest_crime_location = str(top_state.index[0])

        return {
            'total_crimes': total_crimes,
            'states_affected': states_affected,
            'cities_districts': cities,
            'most_common_crime': most_common_crime,
            'highest_crime_location': highest_crime_location,
        }

    def search_locations(self, query):
        """Search for matching locations in the existing dataset."""
        if not query or len(query) < 2:
            return []

        q = query.lower().strip()
        results = []
        seen = set()

        # Search in states
        for state_name in INDIA_STATE_COORDS:
            if q in state_name.lower():
                if state_name not in seen:
                    seen.add(state_name)
                    coords = INDIA_STATE_COORDS[state_name]
                    results.append({
                        'name': state_name,
                        'type': 'State',
                        'lat': coords[0],
                        'lng': coords[1],
                    })

        # Search in cities
        for city_name, state in CITY_TO_STATE.items():
            if q in city_name:
                display = city_name.title()
                if display not in seen:
                    seen.add(display)
                    coords = CITY_COORDS.get(city_name, INDIA_STATE_COORDS.get(state, (0, 0)))
                    results.append({
                        'name': f"{display}, {state}",
                        'type': 'City',
                        'lat': coords[0],
                        'lng': coords[1],
                        'state': state,
                    })

        return results[:20]
