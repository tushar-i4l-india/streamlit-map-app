import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
from folium import IFrame

st.title("Geo Map Chart for I4L Orders Based on Shipping Zip")

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
                return None, None

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

        # Create a Folium map
        m = folium.Map(location=[grouped_df['latitude'].mean(), grouped_df['longitude'].mean()], zoom_start=5)

        # Add points to the map as blue dots
        for _, row in grouped_df.iterrows():
            # popup_content = f"""
            # Order ID: {row['Order ID']}<br>
            # Total: {row['Total']}<br>
            # Quantities: {row['Quantities']}<br>
            # Product Names: {row['Product name']}
            # """
            popup_content = f"""
            <div style="width: 300px;">
                <h4>Order ID: {row['Order ID']}</h4>
                <p><strong>Total:</strong> {row['Total']}</p>
                <p><strong>Quantities:</strong> {row['Quantities']}</p>
                <p><strong>Product Names:</strong> {row['Product name']}</p>
            </div>
            """
            iframe = IFrame(popup_content, width=300, height=200)
            popup = folium.Popup(iframe, max_width=300)
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=1.75,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.6,
                popup=popup,
                tooltip=row[['Total','Order ID', 'Name', 'Quantities']]
            ).add_to(m)

        # Display the map in Streamlit
        st_folium(m, width=800, height=600)
    else:
        st.error(f"The dataset must contain the following columns: {', '.join(required_columns)}")
