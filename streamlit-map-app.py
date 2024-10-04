import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from folium import IFrame

st.title("Geo Map Chart for I4L Orders Based on Shipping ZipCode")

# File uploader widget
uploaded_file = st.file_uploader("Upload Excel File", type="xlsx")

if uploaded_file is not None:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)

    # Ensure the dataset has the required columns
    required_columns = ['Order ID', 'Total', 'Quantities', 'Product name', 'Name', 'Shipping Zip', 'Shipping Province']
    if all(column in df.columns for column in required_columns):
        geolocator = Nominatim(user_agent="geoapiExercises")

        @st.cache_data
        def get_lat_lon(zip_code):
            try:
                location = geolocator.geocode(zip_code)
                return location.latitude, location.longitude
            except:
                return 0, 0

        # Apply the function to the 'Shipping Zip' column with progress bar
        latitudes = []
        longitudes = []
        progress_bar = st.progress(0)
        for i, zip_code in enumerate(df['Shipping Zip']):
            lat, lon = get_lat_lon(zip_code)
            latitudes.append(lat)
            longitudes.append(lon)
            progress_bar.progress((i + 1) / len(df))

        df['latitude'] = latitudes
        df['longitude'] = longitudes

        # Drop rows with missing coordinates
        df = df.dropna(subset=['latitude', 'longitude'])

        # Group by 'Order ID' and aggregate product details
        grouped_df = df.groupby('Order ID').agg({
            'Total': 'sum',
            'Quantities': 'sum',
            'Product name': lambda x: ', '.join(x),
            'Name': 'first',
            'Shipping Zip': 'first',
            'Shipping Province': 'first',
            'latitude': 'first',
            'longitude': 'first'
        }).reset_index()

        # Geocode the specified zip codes
        specified_zip_codes = {
            "London - UB8 2DB": (51.536886, -0.485409),
            "Manchester - OL10 2TA": (53.585153, -2.227689),
            "Birmingham - B38 8SE": (52.409933, -1.940918)
        }
        grouped_df = grouped_df.dropna(subset=['latitude', 'longitude'])
        # Create a Folium map
        m = folium.Map(location=[grouped_df['latitude'].mean(), grouped_df['longitude'].mean()], zoom_start=5)

        # Add circles with 5000-meter radius around the specified zip codes
        for location in specified_zip_codes.values():
            folium.Circle(
                location=location,
                radius=80000,
                color='green',
                fill=True,
                fill_color='green',
                fill_opacity=0.1
            ).add_to(m)

        # Add points to the map as blue dots and highlight those within 50 meters of specified zip codes
        for _, row in grouped_df.iterrows():
            popup_content = f"""
            <div style="width: 300px;">
                <h4>Order ID: {row['Order ID']}</h4>
                <p><strong>Total:</strong> {row['Total']}</p>
                <p><strong>Quantities:</strong> {row['Quantities']}</p>
                <p><strong>Product Names:</strong> {row['Product name']}</p>
                <p><strong>ZipCode:</strong> {row['Shipping Zip']}</p>
            </div>
            """
            iframe = IFrame(popup_content, width=300, height=200)
            popup = folium.Popup(iframe, max_width=300)

            # Check if the point is within 50 meters of any specified zip code
            point = (row['latitude'], row['longitude'])
            within_radius = any(geodesic(point, specified_zip_codes[zip_code]).meters <= 80000 for zip_code in specified_zip_codes)

            # Set color based on whether the point is within the radius
            color = 'red' if within_radius else 'blue'

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=2,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=popup,
                tooltip=row[['Order ID', 'Total', 'Quantities', 'Shipping Zip']]
            ).add_to(m)

        # Display the map in Streamlit
        st_folium(m, width=800, height=600)
    else:
        st.error(f"The dataset must contain the following columns: {', '.join(required_columns)}")
