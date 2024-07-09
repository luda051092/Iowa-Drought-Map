from flask import Flask, render_template
from datetime import datetime, timedelta
import os
import requests
import folium

app = Flask(__name__)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Parameters
area = "CountyStatistics"
statistics_type = "GetDroughtSeverityStatisticsByArea"
aoi = "IA"  # Iowa's state abbreviation for counties
#Get today's date
today = datetime.now()

# Calculate the start of the previous week (last Monday)
start_of_week = today - timedelta(days=today.weekday(), weeks=1)

# Calculate the end of the previous week (last Sunday)
end_of_week = start_of_week + timedelta(days=6)

# Format dates as 'm/d/Y'
start_date = start_of_week.strftime("%m/%d/%Y")
end_date = end_of_week.strftime("%m/%d/%Y")

# Build the URL
url = f"https://usdmdataservices.unl.edu/api/{area}/{statistics_type}?aoi={aoi}&startdate={start_date}&enddate={end_date}&statisticsType=1"

# Function to get coordinates using Google Geocoding API
def get_coordinates(county_name, state):
    geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={county_name},{state}&key={'GOOGLE_API_KEY'}"
    geo_response = requests.get(geo_url)
    if geo_response.status_code == 200:
        geo_data = geo_response.json()
        if geo_data['results']:
            location = geo_data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    return None, None

# Function to get color based on drought severity
def get_color(severity):
    return {
        'D4': 'darkred',
        'D3': 'red',
        'D2': 'orange',
        'D1': 'yellow',
        'D0': 'green',
        'None': 'blue'  # Default color if severity level is unknown
    }.get(severity, 'blue')

@app.route('/')
def index():
    # Make the API request for drought data
    headers = {"Accept": "application/json"}  # Request JSON response
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Process each county in the response data
        drought_data = []
        for county in data:
            county_name = county.get('County')
            # Convert the severity values to floats
            D0 = float(county['D0'])
            D1 = float(county['D1'])
            D2 = float(county['D2'])
            D3 = float(county['D3'])
            D4 = float(county['D4'])

            # Determine the severity level
            severity = 'None'
            if D4 > 0:
                severity = 'D4'
            elif D3 > 0:
                severity = 'D3'
            elif D2 > 0:
                severity = 'D2'
            elif D1 > 0:
                severity = 'D1'
            elif D0 > 0:
                severity = 'D0'
                
            lat, lon = get_coordinates(county_name, "IA")
            
            if lat and lon:
                drought_data.append({
                    'lat': lat,
                    'lon': lon,
                    'severity': severity,
                    'name': county_name,
                    'color': get_color(severity)
                })

        # Create a map centered on Iowa
        iowa_map = folium.Map(location=[42.032974, -93.581543], zoom_start=7)
        
        # Add drought information to the map
        for point in drought_data:
            folium.Marker(
                location=[point['lat'], point['lon']],
                popup=f"{point['name']}: Drought Severity {point['severity']}",
                icon=folium.Icon(color=point['color'], icon='info-sign')
            ).add_to(iowa_map)
        
        # Save the map to an HTML file
        iowa_map.save("templates/iowa_drought_map.html")

    return render_template('index.html')

@app.route('/map')
def map():
    return render_template('iowa_drought_map.html')

if __name__ == '__main__':
    app.run(debug=True)
