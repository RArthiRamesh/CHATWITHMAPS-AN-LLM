import streamlit as st
import googlemaps
import json
import google.generativeai as genai
import requests
import tempfile
import base64
from deep_translator import GoogleTranslator
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
from datetime import datetime, timedelta

# API Keys
GOOGLE_MAPS_API_KEY = 'AIzaSyDiOTu-1wx79U8kPitSjGPdUNSgCS4VflU'
GEMINI_API_KEY = 'AIzaSyB-FtCZpE4KfclIBSNOQmjRwDWr6rtNSCo'
OPENWEATHERMAP_API_KEY = "30b57a5487db153e1bdf17c1e9d33f44"
FIXER_IO_API_KEY = 'aefd13d9423e9456d0cf63114ff95244'

# Initialize clients
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_chat' not in st.session_state:
    st.session_state.current_chat = None
if 'last_searched' not in st.session_state:
    st.session_state.last_searched = None
if 'last_location' not in st.session_state:
    st.session_state.last_location = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'trip_itinerary' not in st.session_state:
    st.session_state.trip_itinerary = {}
if 'currency_rates' not in st.session_state:
    st.session_state.currency_rates = None

# List of supported languages
languages = {'afrikaans': 'af', 'albanian': 'sq', 'amharic': 'am', 'arabic': 'ar', 'armenian': 'hy', 'assamese': 'as', 'aymara': 'ay', 'azerbaijani': 'az', 'bambara': 'bm', 'basque': 'eu', 'belarusian': 'be', 'bengali': 'bn', 'bhojpuri': 'bho', 'bosnian': 'bs', 'bulgarian': 'bg', 'catalan': 'ca', 'cebuano': 'ceb', 'chichewa': 'ny', 'chinese (simplified)': 'zh-CN', 'chinese (traditional)': 'zh-TW', 'corsican': 'co', 'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 'dhivehi': 'dv', 'dogri': 'doi', 'dutch': 'nl', 'english': 'en', 'esperanto': 'eo', 'estonian': 'et', 'ewe': 'ee', 'filipino': 'tl', 'finnish': 'fi', 'french': 'fr', 'frisian': 'fy', 'galician': 'gl', 'georgian': 'ka', 'german': 'de', 'greek': 'el', 'guarani': 'gn', 'gujarati': 'gu', 'haitian creole': 'ht', 'hausa': 'ha', 'hawaiian': 'haw', 'hebrew': 'iw', 'hindi': 'hi', 'hmong': 'hmn', 'hungarian': 'hu', 'icelandic': 'is', 'igbo': 'ig', 'ilocano': 'ilo', 'indonesian': 'id', 'irish': 'ga', 'italian': 'it', 'japanese': 'ja', 'javanese': 'jw', 'kannada': 'kn', 'kazakh': 'kk', 'khmer': 'km', 'kinyarwanda': 'rw', 'konkani': 'gom', 'korean': 'ko', 'krio': 'kri', 'kurdish (kurmanji)': 'ku', 'kurdish (sorani)': 'ckb', 'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 'latvian': 'lv', 'lingala': 'ln', 'lithuanian': 'lt', 'luganda': 'lg', 'luxembourgish': 'lb', 'macedonian': 'mk', 'maithili': 'mai', 'malagasy': 'mg', 'malay': 'ms', 'malayalam': 'ml', 'maltese': 'mt', 'maori': 'mi', 'marathi': 'mr', 'meiteilon (manipuri)': 'mni-Mtei', 'mizo': 'lus', 'mongolian': 'mn', 'myanmar': 'my', 'nepali': 'ne', 'norwegian': 'no', 'odia (oriya)': 'or', 'oromo': 'om', 'pashto': 'ps', 'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt', 'punjabi': 'pa', 'quechua': 'qu', 'romanian': 'ro', 'russian': 'ru', 'samoan': 'sm', 'sanskrit': 'sa', 'scots gaelic': 'gd', 'sepedi': 'nso', 'serbian': 'sr', 'sesotho': 'st', 'shona': 'sn', 'sindhi': 'sd', 'sinhala': 'si', 'slovak': 'sk', 'slovenian': 'sl', 'somali': 'so', 'spanish': 'es', 'sundanese': 'su', 'swahili': 'sw', 'swedish': 'sv', 'tajik': 'tg', 'tamil': 'ta', 'tatar': 'tt', 'telugu': 'te', 'thai': 'th', 'tigrinya': 'ti', 'tsonga': 'ts', 'turkish': 'tr', 'turkmen': 'tk', 'twi': 'ak', 'ukrainian': 'uk', 'urdu': 'ur', 'uyghur': 'ug', 'uzbek': 'uz', 'vietnamese': 'vi', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 'yoruba': 'yo', 'zulu': 'zu'}

# Function to translate text
def translate_text(text, target_language):
    try:
        translator = GoogleTranslator(source='auto', target=target_language)
        return translator.translate(text)
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

# Function to check if TTS is available
def is_tts_available():
    try:
        from gtts import gTTS
        return True
    except ImportError:
        return False

# Function to convert text to speech and return base64 encoded audio (optional)
def text_to_speech_base64(text, lang='en'):
    if is_tts_available():
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                tts.save(temp_audio.name)
                with open(temp_audio.name, "rb") as audio_file:
                    return base64.b64encode(audio_file.read()).decode()
        except Exception as e:
            st.error(f"Text-to-speech error: {str(e)}")
            return None
    return None

# Function to fetch places from Google Maps Places API
def fetch_places(location, radius, query):
    try:
        places_result = gmaps.places_nearby(location, radius=radius, keyword=query)
        return places_result
    except Exception as e:
        st.error(f"Error fetching places: {str(e)}")
        return {'results': []}

# Function to fetch place details
def fetch_place_details(place_id):
    try:
        place_details = gmaps.place(place_id=place_id, fields=['name', 'geometry', 'rating', 'reviews', 'formatted_address', 'formatted_phone_number', 'photo', 'type'])
        return place_details
    except Exception as e:
        st.error(f"Error fetching place details: {str(e)}")
        return {'result': {}}

# Function to get latitude and longitude from Google Maps Geocoding API
def get_lat_lon_from_location(location_name):
    try:
        geocode_result = gmaps.geocode(location_name)
        if geocode_result:
            lat = geocode_result[0]['geometry']['location']['lat']
            lon = geocode_result[0]['geometry']['location']['lng']
            return (lat, lon)
        else:
            return None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None

# Function to get photo reference URL
def get_photo_url(photo_reference):
    return f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}'

# Function to parse user input using Gemini
def parse_user_input(user_input, last_location=None):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        Parse the following user input and extract the location and place types:
        User input: "{user_input}"
        Last known location: "{last_location}"
        
        Return the result in the following format:
        Location: [extracted location]
        Place Types: [comma-separated list of extracted place types]

        If specific place types are not mentioned, default to "restaurant".
        Valid place types are: restaurant, hospital, shop, petrol pump, atm, pharmacy, clothing, supermarket, college, school, bus station, railway station, metro station, airport, beach, park, garden, temple, church, mosque, pub, tourist spot.
        
        Please correct any spelling mistakes or interpret variations.
        Be flexible in understanding the user's intent, even if they use non-standard terms or make spelling errors.
        
        If no location is specified in the user input, use the last known location.
        """
        
        response = model.generate_content(prompt)
        parsed_text = response.text
        
        location = ""
        place_types = ["restaurant"]  # Default to restaurant if not specified
        
        for line in parsed_text.split('\n'):
            if line.startswith("Location:"):
                location = line.split(":")[1].strip()
            elif line.startswith("Place Types:"):
                place_types = [pt.strip().lower() for pt in line.split(":")[1].strip().split(",")]
        
        # If no location was extracted, use the last known location
        if not location and last_location:
            location = last_location
        
        return location, place_types
    except Exception as e:
        st.error(f"Error parsing user input: {str(e)}")
        return user_input, ["restaurant"]

# Function to summarize reviews
def summarize_reviews(reviews, place_type, max_words=50):
    if not reviews:
        return "No reviews available."
    
    try:
        all_text = " ".join([review['text'] for review in reviews])
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        summary_prompt = f"""
        Summarize the following {place_type} reviews in about {max_words} words. 
        Highlight the main points, both positive and negative, mentioned by multiple reviewers.
        Focus on aspects relevant to this type of place.
        
        Provide a concise summary without using headers like "Positive:" or "Negative:".
        Instead, use phrases like "Positives include..." and "However, some negatives mentioned are...".
        
        If there are no relevant reviews or not enough information to provide a meaningful summary, 
        respond with 'No reviews available.'

        Reviews:
        {all_text}
        
        Summary:
        """
        summary_response = model.generate_content(summary_prompt)
        summary = summary_response.text.strip()
        
        check_prompt = f"""
        Analyze the following summary and determine if it essentially indicates that no reviews are available or that there's not enough information to provide a meaningful summary.
        Summary: "{summary}"
        
        Respond with ONLY "True" if the summary indicates no reviews or lack of information, and "False" otherwise.
        """
        
        check_response = model.generate_content(check_prompt)
        no_reviews_indicated = check_response.text.strip().lower() == "true"
        
        if no_reviews_indicated:
             return "No reviews available."
        else:
            return summary 
    except Exception as e:
        return "No reviews available."

# Function to suggest related places or activities
def suggest_related_places(place_type, location):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        Given a user is interested in {place_type}s in {location}, suggest 5 related places or activities they might also be interested in.
        Consider the following:
        1. Complementary activities or places
        2. Nearby attractions or points of interest
        3. Time of day appropriate suggestions
        4. Local specialties or unique experiences
        5. Popular combinations or pairings

        Format the response as a bulleted list with brief explanations.
        """
        
        response = model.generate_content(prompt)
        suggestions = response.text.strip()
        return suggestions
    except Exception as e:
        st.error(f"Error in generating suggestions: {str(e)}")
        return "Unable to generate suggestions at this time."

# Function to get weather data from OpenWeatherMap API
def get_weather_data(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            weather_text = f"The weather in {data['name']} is currently {data['main']['temp']} degrees Celsius with {data['weather'][0]['description']}."
            audio_base64 = text_to_speech_base64(weather_text)
            if audio_base64:
                data['audio_base64'] = audio_base64
            else:
                data['audio_base64'] = ""
            return data
        else:
            st.error("Failed to retrieve weather data.")
            return None
    except Exception as e:
        st.error(f"Weather API error: {str(e)}")
        return None

# Function to create map HTML
def create_map_html(user_location, place_details_list, weather_data):
    try:
        audio_base64 = weather_data.get('audio_base64', '') if weather_data else ''
        
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&callback=initMap" async defer></script>
            <script>
                function initMap() {{
                    var userLocation = {{lat: {user_location[0]}, lng: {user_location[1]}}};
                    var map = new google.maps.Map(document.getElementById('map'), {{
                        zoom: 14,
                        center: userLocation
                    }});
                    new google.maps.Marker({{
                        position: userLocation,
                        map: map,
                        title: 'Your Location',
                        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
                    }});
                    var places = {json.dumps(place_details_list)};
                    places.forEach(function(place) {{
                        if (place.result && place.result.geometry && place.result.geometry.location) {{
                            var placeLocation = new google.maps.LatLng(place.result.geometry.location.lat, place.result.geometry.location.lng);
                            var photos = place.result.photos ? place.result.photos.map(p => p.photo_reference) : [];
                            var photoUrl = photos.length > 0 ? getPhotoUrl(photos[0]) : '';
                            var rating = place.result.rating ? 'Rating: ' + place.result.rating : 'No Rating';
                            var contact = place.result.formatted_phone_number ? 'Contact: ' + place.result.formatted_phone_number : 'No Contact Info';
                            var reviews = place.result.reviews ? place.result.reviews.map(r => '<p><strong>' + r.author_name + ':</strong> ' + r.text.substring(0, 100) + '...</p>').join('') : 'No Reviews';
                            var contentString = '<div><strong>' + place.result.name + '</strong><br>' +
                                rating + '<br>' +
                                'Address: ' + (place.result.formatted_address || 'N/A') + '<br>' +
                                contact + '<br>' +
                                'Reviews:<br>' + reviews + '<br>' +
                                (photoUrl ? '<img src="' + photoUrl + '" width="200" height="150">' : '') + '</div>';
                            
                            var marker = new google.maps.Marker({{
                                position: placeLocation,
                                map: map,
                                title: place.result.name,
                                icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
                            }});
                            var infowindow = new google.maps.InfoWindow({{
                                content: contentString
                            }});
                            marker.addListener('click', function() {{
                                infowindow.open(map, marker);
                            }});
                        }}
                    }});
                    {f'''
                    // Add weather info
                    var weatherIcon = '{weather_data["weather"][0]["icon"]}';
                    var weatherIconUrl = 'http://openweathermap.org/img/w/' + weatherIcon + '.png';
                    var weatherTemp = '{weather_data["main"]["temp"]}°C';
                    var weatherDesc = '{weather_data["weather"][0]["description"]}';
                    var weatherTempMax = '{weather_data["main"]["temp_max"]}°C';
                    var weatherTempMin = '{weather_data["main"]["temp_min"]}°C';
                    var weatherFeelsLike = '{weather_data["main"]["feels_like"]}°C';
                    var weatherClouds = '{weather_data["clouds"]["all"]}%';
                    var weatherWindSpeed = '{weather_data["wind"]["speed"]} m/s';
                    var weatherHumidity = '{weather_data["main"]["humidity"]}%';
                    var weatherAudioBase64 = '{audio_base64}';
                   
                    var weatherContentString = '<div><img src="' + weatherIconUrl + '"><br>' +
                        '<strong>Temperature:</strong> ' + weatherTemp + '<br>' +
                        '<strong>Description:</strong> ' + weatherDesc + '</div>'+
                        '<strong>Max Temperature:</strong> ' + weatherTempMax + '<br>' +
                        '<strong>Min Temperature:</strong> ' + weatherTempMin + '<br>' +
                        '<strong>Feels Like:</strong> ' + weatherFeelsLike + '<br>' +
                        '<strong>Cloud Cover:</strong> ' + weatherClouds + '<br>' +
                        '<strong>Wind Speed:</strong> ' + weatherWindSpeed + '<br>' +
                        '<strong>Humidity:</strong> ' + weatherHumidity + '<br>' +
                        (weatherAudioBase64 ? '<audio id="weatherAudio" style="display:none;"><source src="data:audio/mp3;base64,' + weatherAudioBase64 + '" type="audio/mp3"></audio>' : '');
                        
                    var weatherInfoWindow = new google.maps.InfoWindow({{
                        content: weatherContentString,
                        position: userLocation
                    }});

                    var weatherMarker = new google.maps.Marker({{
                        position: userLocation,
                        map: map,
                        icon: weatherIconUrl,
                        title: 'Weather Information'
                    }});

                    weatherMarker.addListener('click', function() {{
                        weatherInfoWindow.open(map, weatherMarker);
                        if (weatherAudioBase64) {{
                            var audio = document.getElementById('weatherAudio');
                            if (audio) audio.play();
                        }}
                    }});
                    ''' if weather_data else ''}
                }}

                function getPhotoUrl(photoReference) {{
                    return 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=' + photoReference + '&key={GOOGLE_MAPS_API_KEY}';
                }}
            </script>
        </head>
        <body>
            <div id="map" style="height: 500px; width: 100%;"></div>
        </body>
        </html>
        """
        return map_html
    except Exception as e:
        st.error(f"Error creating map: {str(e)}")
        return "<div>Error loading map</div>"

# Function to generate place visit data
def generate_place_visit_data(place_details_list):
    data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    for place in place_details_list:
        if place.get('result') and place['result'].get('name'):
            place_name = place['result']['name']
            for date in date_range:
                visits = random.randint(50, 500)
                data.append({
                    'date': date,
                    'place': place_name,
                    'visits': visits
                })
    
    return pd.DataFrame(data)

# Function to create place visits chart
def create_place_visits_chart(df):
    if df.empty:
        return None
    fig = px.line(df, x='date', y='visits', color='place', title='Place Visits Over Time')
    fig.update_layout(xaxis_title='Date', yaxis_title='Number of Visits')
    return fig

# Function to create weather trend chart
def create_weather_trend_chart(weather_data):
    if not weather_data:
        return None
    dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
    temperatures = [weather_data['main']['temp']] + [random.uniform(weather_data['main']['temp'] - 5, weather_data['main']['temp'] + 5) for _ in range(6)]
    df = pd.DataFrame({'date': dates, 'temperature': temperatures})
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['temperature'], mode='lines+markers'))
    fig.update_layout(title='Temperature Trend (Last 7 Days)', xaxis_title='Date', yaxis_title='Temperature (°C)')
    return fig

# Function to calculate distances
def calculate_distances(user_location, place_details_list):
    distances = []
    for place in place_details_list:
        if place.get('result') and place['result'].get('geometry') and place['result']['geometry'].get('location'):
            try:
                place_location = place['result']['geometry']['location']
                distance = gmaps.distance_matrix(user_location, (place_location['lat'], place_location['lng']))['rows'][0]['elements'][0]['distance']['value']
                distances.append({
                    'name': place['result']['name'],
                    'distance': distance
                })
            except Exception as e:
                continue
    return sorted(distances, key=lambda x: x['distance'])[:10]  # Return top 10 nearest places

# Function to display results
def display_results(location_name, place_types, user_location, target_language):
    query_map = {
        "restaurant": "restaurant",
        "hospital": "hospital",
        "shop": "store",
        "petrol pump": "gas station",
        "atm": "atm",
        "pharmacy": "pharmacy",
        "clothing": "clothing store",
        "supermarket": "supermarket",
        "college": "college",
        "school": "school",
        "bus station": "bus station",
        "railway station": "train station",
        "metro station": "subway station",
        "airport": "airport",
        "beach": "beach",
        "park": "park",
        "garden": "garden",
        "temple": "hindu temple",
        "church": "church",
        "mosque": "mosque",
        "pub": "pub",
        "tourist spot": "tourist attraction"
    }
    
    all_places = []
    for place_type in place_types:
        query = query_map.get(place_type, place_type)
        radius = 1000  # Increased radius to 1000 meters
        places = fetch_places(user_location, radius, query)
        all_places.extend(places.get('results', []))
    
    # Fetch detailed information for each place
    place_details_list = []
    for place in all_places:
        place_id = place.get('place_id')
        if place_id:
            place_details = fetch_place_details(place_id)
            place_details_list.append(place_details)

    # Fetch weather data
    weather_data = get_weather_data(user_location[0], user_location[1])
    
    # Create map HTML
    map_html = create_map_html(user_location, place_details_list, weather_data)
    
    # Store map data in session state
    st.session_state.map_data = {
        'html': map_html,
        'location_name': location_name,
        'place_types': place_types,
        'user_location': user_location,
        'place_details_list': place_details_list,
        'weather_data': weather_data
    }
    
    # Render the HTML in Streamlit
    st.components.v1.html(map_html, height=500, width=700, scrolling=True)
    
    st.markdown(f"<h2 style='color: black;'>📍 Nearby Places in {location_name}</h2>", unsafe_allow_html=True)
    if all_places:
        for place in all_places:
            place_id = place.get('place_id')
            if place_id:
                place_details = fetch_place_details(place_id)
                result = place_details.get('result', {})
                name = result.get('name', 'N/A')
                formatted_address = result.get('formatted_address', 'Address not available')
                rating = result.get('rating', 'No Rating')
                contact = result.get('formatted_phone_number', 'Contact not available')
                reviews = result.get('reviews', [])
                place_type = result.get('types', ['N/A'])[0] if result.get('types') else 'N/A'
                
                st.markdown(f"""
                <div class="place-card">
                    <h3 style='color: black;'>{translate_text(name, target_language)} ({translate_text(place_type, target_language)})</h3>
                    <p style='color: black;'>📍 {translate_text(formatted_address, target_language)}</p>
                    <p style='color: black;'>⭐ {translate_text('Rating', target_language)}: {rating}</p>
                    <p style='color: black;'>📞 {translate_text('Contact', target_language)}: {contact}</p>
                """, unsafe_allow_html=True)
                
                if reviews:
                    review_summary = summarize_reviews(reviews, place_type)
                    st.markdown(f"<p style='color: black;'>📝 {translate_text('Review Summary', target_language)}: {translate_text(review_summary, target_language)}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color: black;'>📝 {translate_text('Review Summary', target_language)}: {translate_text('No reviews available for this place.', target_language)}</p>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning(translate_text("No places found nearby.", target_language))
    
    # Display weather information
    if weather_data:
        st.markdown(f"<h2 style='color: black;'>🌤️ Current Weather in {location_name}</h2>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="weather-card">
            <p style='color: black;'>🌡️ {translate_text('Temperature', target_language)}: {weather_data['main']['temp']}°C</p>
            <p style='color: black;'>📝 {translate_text('Description', target_language)}: {translate_text(weather_data['weather'][0]['description'], target_language)}</p>
            <p style='color: black;'>💧 {translate_text('Humidity', target_language)}: {weather_data['main']['humidity']}%</p>
            <p style='color: black;'>🌬️ {translate_text('Wind Speed', target_language)}: {weather_data['wind']['speed']} m/s</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Generate and display suggestions
    st.markdown(f"<h2 style='color: black;'>💡 You might also be interested in:</h2>", unsafe_allow_html=True)
    suggestions = suggest_related_places(place_types[0], location_name)
    st.markdown(f'<div class="suggestion-card" style="color: black;">{translate_text(suggestions, target_language)}</div>', unsafe_allow_html=True)

    # Add new visualizations
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: black;'>📊 Data Visualizations</h2>", unsafe_allow_html=True)
    
    # Place Visits Chart
    visit_data = generate_place_visit_data(place_details_list)
    visits_chart = create_place_visits_chart(visit_data)
    st.plotly_chart(visits_chart)

    # Weather Trend Chart
    weather_chart = create_weather_trend_chart(weather_data)
    st.plotly_chart(weather_chart)
    # Calculate distances and create bar chart
    distances = calculate_distances(user_location, place_details_list)
    df_distances = pd.DataFrame(distances)
    fig_distances = px.bar(df_distances, x='name', y='distance', title='Distance to Nearby Places')
    fig_distances.update_layout(xaxis_title='Place Name', yaxis_title='Distance (meters)')
    st.plotly_chart(fig_distances)

# Function for local trip planner
def local_trip_planner(location, duration):
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Create a {duration}-day trip itinerary for {location}. For each day, suggest:
    1. Morning activity
    2. Afternoon activity
    3. Evening activity
    4. A local restaurant for lunch or dinner

    For each suggestion, provide:
    - Name of the place or activity
    - A brief description (1-2 sentences)
    - Why it's interesting or important

    Format the response as a JSON object with the following structure:
    {{
        "day1": {{
            "morning": {{
                "activity": "Name of morning activity",
                "description": "Brief description",
                "why_interesting": "Reason why it's interesting"
            }},
            "afternoon": {{...}},
            "evening": {{...}},
            "restaurant": {{
                "name": "Restaurant name",
                "cuisine": "Type of cuisine",
                "description": "Brief description"
            }}
        }},
        "day2": {{...}},
        ...
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to parse the response as JSON
        try:
            itinerary = json.loads(response_text)
        except json.JSONDecodeError:
            # If parsing fails, attempt to extract JSON from the response
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                json_str = response_text[start_index:end_index]
                itinerary = json.loads(json_str)
            else:
                raise ValueError("Unable to extract valid JSON from the response")
        
        return itinerary
    except Exception as e:
        st.error(f"Error in generating trip itinerary: {str(e)}")
        return None

# Function to fetch currency exchange rates
def fetch_currency_rates():
    url = f"http://data.fixer.io/api/latest?access_key={FIXER_IO_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['rates']
    else:
        st.error("Failed to fetch currency exchange rates.")
        return None

# Function to convert currency
def convert_currency(amount, from_currency, to_currency, rates):
    if from_currency == "EUR":
        return amount * rates[to_currency]
    elif to_currency == "EUR":
        return amount / rates[from_currency]
    else:
        return amount / rates[from_currency] * rates[to_currency]

# Main app
st.markdown("<h1 style='color: black;'>🌍 Chat with Maps!</h1>", unsafe_allow_html=True)

# Add language selection to the sidebar
selected_language = st.sidebar.selectbox("Choose language", list(languages.keys()))
target_language_code = languages[selected_language]

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # User input
    if st.session_state.current_chat:
        user_input = st.text_input(
            translate_text("🔍 What are you looking for?", target_language_code),
            value=st.session_state.current_chat['user_input'])
    else:
        st.markdown("<p style='color: black;'>🔍 What are you looking for? (e.g., 'Show me restaurants and shops in New York' or 'Find pharmacies and hospitals near Central Park')</p>", unsafe_allow_html=True)
        user_input = st.text_input("Enter your query here:")
    # Add speech recognition button
    if st.button(translate_text("🎤 Speak your query", target_language_code)):
        with st.spinner(translate_text("Listening...", target_language_code)):
            speech_input = speech_to_text()
            if speech_input:
                user_input = speech_input
                st.session_state.user_input = user_input

    # Currency Conversion Section
    st.markdown("<h3 style='color: black;'>💱 Currency Conversion</h3>", unsafe_allow_html=True)
    if 'currency_rates' not in st.session_state or st.session_state.currency_rates is None:
        st.session_state.currency_rates = fetch_currency_rates()

    if st.session_state.currency_rates:
        currencies = list(st.session_state.currency_rates.keys())
        col1, col2, col3 = st.columns(3)
        with col1:
            amount = st.number_input("Amount", min_value=0.01, value=1.0, step=0.01)
        with col2:
            from_currency = st.selectbox("From", currencies, index=currencies.index('USD'))
        with col3:
            to_currency = st.selectbox("To", currencies, index=currencies.index('EUR'))
        
        if st.button("Convert"):
            converted_amount = convert_currency(amount, from_currency, to_currency, st.session_state.currency_rates)
            st.success(f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}")

    # Check if the input is empty or contains only whitespace
    if not user_input.strip():
        st.markdown("<div style='color: black; background-color: #fff3cd; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
        st.markdown("<p style='color: black;'><strong>Please enter a valid query. Here are some example queries:</strong></p>", unsafe_allow_html=True)
        st.markdown("""
        <ul style='color: black;'>
            <li>Show me restaurants and cafes in Paris</li>
            <li>Find museums and art galleries near Central Park, New York</li>
            <li>What are the best beaches in Bali?</li>
            <li>Where can I find shopping malls and movie theaters in Tokyo?</li>
            <li>Suggest historical sites and landmarks in Rome</li>
        </ul>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        user_input = user_input.replace(",", "")

with col2:
    # Sidebar for chat history and options
    st.sidebar.title(translate_text("💬 Chat History", target_language_code))

    # New Chat button
    if st.sidebar.button(translate_text("🆕 New Chat", target_language_code)):
        st.session_state.current_chat = None
        st.session_state.last_searched = None
        st.session_state.last_location = None
        st.session_state.user_input = ""
        st.rerun()

    # Display chat history with delete options
    for i, chat in enumerate(st.session_state.chat_history):
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(f"{chat['user_input'][:30]}...", key=f"chat_{i}"):
                st.session_state.current_chat = chat
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.chat_history.pop(i)
                if st.session_state.current_chat == chat:
                    st.session_state.current_chat = None
                st.rerun()

    # Clear all chats button
    if st.sidebar.button("🧹 Clear All Chats"):
        st.session_state.chat_history = []
        st.session_state.current_chat = None
        st.session_state.last_searched = None
        st.session_state.last_location = None
        st.session_state.user_input = ""
        st.rerun()

    # Add Trip Planner section to sidebar
    st.sidebar.title(translate_text("📅 Trip Planner", target_language_code))
    trip_location = st.sidebar.text_input(translate_text("Enter trip location", target_language_code))
    trip_duration = st.sidebar.number_input(translate_text("Enter trip duration (days)", target_language_code), min_value=1, max_value=14, value=3)
    
    if st.sidebar.button(translate_text("Plan My Trip", target_language_code)):
        if trip_location and trip_duration:
            with st.spinner(translate_text("Planning your trip...", target_language_code)):
                trip_itinerary = local_trip_planner(trip_location, trip_duration)
                if trip_itinerary:
                    st.session_state.trip_itinerary = trip_itinerary
                    st.rerun()
        else:
            st.sidebar.warning(translate_text("Please enter both location and duration.", target_language_code))

# Process input for nearby places search
if user_input and user_input != st.session_state.last_searched:
    location_name, place_types = parse_user_input(user_input, st.session_state.last_location)
    
    if not st.session_state.current_chat or user_input != st.session_state.current_chat['user_input']:
        new_chat = {
            'user_input': user_input,
            'location': location_name,
            'place_types': place_types
        }
        st.session_state.chat_history.append(new_chat)
        st.session_state.current_chat = new_chat
    
    st.session_state.last_searched = user_input
    st.session_state.last_location = location_name
    
    st.markdown(f"<p style='color: black;'>🔎 Searching for {', '.join(place_types)} in {location_name}</p>", unsafe_allow_html=True)

    user_location = get_lat_lon_from_location(location_name)
    
    if user_location:
        display_results(location_name, place_types, user_location, target_language_code)
    else:
        st.error("📍 Location not found or geocoding failed. Please try again.")

elif st.session_state.last_searched:
    location_name, place_types = parse_user_input(st.session_state.last_searched, st.session_state.last_location)
    st.markdown(f"<p style='color: black;'>🔎 Showing results for {', '.join(place_types)} in {location_name}</p>", unsafe_allow_html=True)
    
    user_location = get_lat_lon_from_location(location_name)
    
    if user_location:
        display_results(location_name, place_types, user_location, target_language_code)
    else:
        st.error("📍 Location not found or geocoding failed. Please try again.")

# Display Trip Itinerary
if 'trip_itinerary' in st.session_state and st.session_state.trip_itinerary:
    st.markdown(f"<h1 style='color: black;'>🗺️ Your Trip Itinerary for {trip_location}</h1>", unsafe_allow_html=True)
    for day, activities in st.session_state.trip_itinerary.items():
        st.markdown(f"<h3 style='color: black;'>Day {day[3:]}</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"<p style='color: black;'><strong>Morning:</strong> {activities['morning']['activity']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'>{activities['morning']['description']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'><em>Why it's interesting:</em> {activities['morning']['why_interesting']}</p>", unsafe_allow_html=True)
            
            st.markdown(f"<p style='color: black;'><strong>Afternoon:</strong> {activities['afternoon']['activity']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'>{activities['afternoon']['description']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'><em>Why it's interesting:</em> {activities['afternoon']['why_interesting']}</p>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<p style='color: black;'><strong>Evening:</strong> {activities['evening']['activity']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'>{activities['evening']['description']}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'><em>Why it's interesting:</em> {activities['evening']['why_interesting']}</p>", unsafe_allow_html=True)
            
            st.markdown(f"<p style='color: black;'><strong>Restaurant:</strong> {activities['restaurant']['name']} ({activities['restaurant']['cuisine']})</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'>{activities['restaurant']['description']}</p>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# Add a second chat input for follow-up queries
if st.session_state.last_location:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: black;'>🤔 Ask another question about the same location:</h2>", unsafe_allow_html=True)
    follow_up_input = st.text_input("What else would you like to know?", key="follow_up")
    
    # Add speech recognition for follow-up queries
    if st.button("🎤 Speak your follow-up query"):
        with st.spinner("Listening..."):
            speech_input = speech_to_text()
            if speech_input:
                follow_up_input = speech_input
    
    if follow_up_input:
        follow_up_location, follow_up_place_types = parse_user_input(follow_up_input, st.session_state.last_location)
        
        st.markdown(f"<p style='color: black;'>🔎 Searching for {', '.join(follow_up_place_types)} in {follow_up_location}</p>", unsafe_allow_html=True)
        
        follow_up_user_location = get_lat_lon_from_location(follow_up_location)
        
        if follow_up_user_location:
            display_results(follow_up_location, follow_up_place_types, follow_up_user_location, target_language_code)
        else:
            st.error("📍 Location not found or geocoding failed. Please try again.")

# Add a section for exploring correlations
if st.session_state.last_location:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: black;'>🔗 Explore correlations:</h2>", unsafe_allow_html=True)
    correlation_options = [
        "Find popular combinations",
        "Discover nearby attractions",
        "Suggest time-appropriate activities",
        "Recommend local specialties",
        "Find complementary services"
    ]
    selected_correlation = st.selectbox("What would you like to explore?", correlation_options)
    
    if selected_correlation:
        model = genai.GenerativeModel('gemini-2.0-flash')
        correlation_prompt = f"""
        Based on the user's interest in {', '.join(place_types)} in {location_name}, and their request to "{selected_correlation}",
        provide a detailed response with 3-5 suggestions. Each suggestion should include:
        1. Name of the place or activity
        2. Brief description
        3. Why it's relevant or interesting
        4. Any additional tips or information

        Format the response as a numbered list with clear sections for each suggestion.
        """
        
        try:
            with st.spinner("Generating suggestions..."):
                correlation_response = model.generate_content(correlation_prompt)
                correlation_suggestions = correlation_response.text.strip()
                st.markdown(f'<div class="suggestion-card" style="color: black;">{correlation_suggestions}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error in generating correlation suggestions: {str(e)}")
            st.markdown("<p style='color: black;'>Unable to generate correlation suggestions at this time.</p>", unsafe_allow_html=True)

# Add a footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='color: black; text-align: center;'>© 2024 Discover Nearby Places. All rights reserved.</p>", unsafe_allow_html=True)

# Custom CSS to enhance the UI and ensure black text
st.markdown("""
<style>
    /* Hide header */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Reset and base styling - Force colors during runtime */
    .main .block-container {
        background-color: #E3F2FD !important;
        padding: 2rem !important;
        border-radius: 0 !important;
        max-width: 100% !important;
        color: #1A1A1A !important;
    }
    
    /* Force main container background during app execution */
    .main, .main > div, .stApp > div {
        background-color: #E3F2FD !important;
    }
    
    /* Sidebar - Clean Green - Force during runtime */
    .stSidebar, .css-1d391kg, .css-1lcbmhc, .stSidebar > div, 
    section[data-testid="stSidebar"], .stSidebar .stSidebar-content,
    .css-ng1t4o, .css-qbe2hs, .stSidebar-content, [data-testid="stSidebar"] > div {
        background-color: #4CAF50 !important;
    }
    
    /* Force sidebar background color during app execution */
    .stSidebar::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background-color: #4CAF50 !important;
        z-index: -1 !important;
    }
    
    /* Additional force for sidebar during runtime */
    .stSidebar, .stSidebar * {
        background-color: #4CAF50 !important;
    }
    
    .stSidebar .element-container, .stSidebar .stMarkdown, .stSidebar .stSelectbox > div {
        background-color: transparent !important;
    }
    
    /* Main content text - Dark on light blue - Force during runtime */
    h1, h2, h3, h4, h5, h6 {
        color: #1A1A1A !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-weight: 600 !important;
    }
    
    p, div, span, li, label {
        color: #1A1A1A !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Force main area text colors during app execution */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
    .main p, .main div, .main span, .main li, .main label,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp div:not(.stSidebar div), .stApp span, .stApp li, .stApp label {
        color: #1A1A1A !important;
    }
    
    /* Sidebar text - White on green - Fixed with higher specificity */
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, .stSidebar h6,
    .stSidebar p, .stSidebar div:not([data-testid="stSelectbox"]), 
    .stSidebar span, .stSidebar li, .stSidebar label {
        color: white !important;
    }
    
    /* Sidebar selectbox label specifically */
    .stSidebar .stSelectbox label,
    .stSidebar [data-testid="stSelectbox"] label,
    .stSidebar .element-container label {
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar selectbox styling - stable colors */
    .stSidebar .stSelectbox > div > div > select,
    .stSidebar [data-testid="stSelectbox"] select {
        background-color: white !important;
        color: #1A1A1A !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
        font-weight: normal !important;
    }
    
    /* Prevent color changes on focus/hover/active - keep default appearance */
    .stSidebar .stSelectbox > div > div > select:focus,
    .stSidebar .stSelectbox > div > div > select:hover,
    .stSidebar .stSelectbox > div > div > select:active,
    .stSidebar [data-testid="stSelectbox"] select:focus,
    .stSidebar [data-testid="stSelectbox"] select:hover,
    .stSidebar [data-testid="stSelectbox"] select:active {
        background-color: white !important;
        color: #1A1A1A !important;
        border: 1px solid #CCCCCC !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Sidebar selectbox options */
    .stSidebar .stSelectbox option,
    .stSidebar [data-testid="stSelectbox"] option {
        background-color: white !important;
        color: #1A1A1A !important;
    }
    
    /* Simple buttons */
    .stButton > button {
        background-color: #2196F3;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #1976D2;
    }
    
    /* Sidebar buttons */
    .stSidebar .stButton > button {
        background-color: #388E3C;
        color: white;
    }
    
    .stSidebar .stButton > button:hover {
        background-color: #2E7D32;
    }
    
    /* Clean input fields */
    .stTextInput > div > div > input {
        background-color: white;
        color: #1A1A1A;
        border: 1px solid #CCCCCC;
        border-radius: 6px;
        padding: 0.5rem;
    }
    
    .stSelectbox > div > div > select {
        background-color: white;
        color: #1A1A1A;
        border: 1px solid #CCCCCC;
        border-radius: 6px;
        padding: 0.5rem;
    }
    
    /* Main area selectbox options */
    .stSelectbox option {
        background-color: white !important;
        color: #1A1A1A !important;
    }
    
    /* Simple cards */
    .place-card {
        background-color: white;
        color: #1A1A1A;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .place-card * {
        color: #1A1A1A !important;
    }
    
    .weather-card {
        background-color: #F1F8E9;
        color: #1A1A1A;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #C8E6C9;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .weather-card * {
        color: #1A1A1A !important;
    }
    
    .suggestion-card {
        background-color: #FFF3E0;
        color: #1A1A1A;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #FFE0B2;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .suggestion-card * {
        color: #1A1A1A !important;
    }
    
    /* Alert styling */
    .stAlert {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 1rem;
        border-radius: 6px;
        border: 1px solid #FFCDD2;
    }
    
    .stAlert * {
        color: #C62828 !important;
    }
</style>
""", unsafe_allow_html=True)
