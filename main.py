"""
Matthew Baillie
CS230 - 4
Professor Anqi Xu
Final Project
"""
import os
import streamlit as st
import pandas as pd
# import pydeck as pdk
import folium as fm
import matplotlib.pyplot as plt
current_dir = os.path.dirname(os.path.abspath(__file__))


def openProjectCsv(filename, index=None, dir=current_dir):
    """
    open as csv file from a given directory (default is just the projec folder).

    filename: name of the csv file with or without the .csv
    index: key for the column that will represent the index for the dataframe
    dir: directory to search for the given file. default is the directory this .py file is within
    """

    # handling to make sure filename is a csv
    if not filename.endswith(".csv"):
        filename += ".csv"
    
    file = os.path.join(dir, filename)
    # [PY3]
    try:
        return pd.read_csv(file, index_col=index)
    except FileNotFoundError:
        print(f"'{filename}' not found in '{dir}'")

df = openProjectCsv("data/skyscrapers", "id")

st.set_page_config(page_title="Skyscrapers in the US", page_icon="🏙️")

# Used chatGPT to write CSS classes for webpage
st.markdown( # [ST4] custom CSS classes using streamlit markdown
    """
<style>
/* Styling for the title */
.title {
    font-family: 'Roboto', sans-serif;
    color: white;
    font-weight: bold;
    font-size: 60px;  /* Increased font size for larger title */
    text-align: center;  /* Center the text */
    margin-top: 50px;  /* Add space from the top */
}

/* Styling for centering and making the DataFrame wider */
.dataframe-container {
    display: flex;
    justify-content: center;
    margin-top: 20px;
}
.dataframe-container table {
    width: 100%;
    max-width: 1200px;
}

/* Styling for regular paragraph text */
.regular-text {
    font-family: 'Roboto', sans-serif;
    color: white;
    font-weight: normal;  /* Not bold */
    font-size: 26px;  /* Regular text size */
    padding-top: 20px;  /* Padding at the top */
    padding-left: 20px;  /* Padding on the left */
    padding-right: 20px;  /* Padding on the right */
    text-align: left;  /* Optional: center text if needed */
}
</style>
    """,
    unsafe_allow_html=True
)

# Webpage header:
st.markdown("<div class='title'>Skyscrapers in the US </div>", unsafe_allow_html=True)

# make a copy so we can freely edit it for the map
df_map = df

# set up a color key for building status
status_colors = {
    "completed": "green",
    "under construction": "red",
    "on hold": "red",
    "never completed": "red",
    "vision": "grey",
    "proposed": "grey",
    "architecturally topped out": "yellow",
    "structurally topped out": "yellow",
    "demolished": "white"
}
# populate this color key across the dataframe
df_map["color"] = df_map["status.current"].map(status_colors).fillna("black") # [DA9]
# remove anything that cant be plotted correctly
df_map = df_map[
    (df_map["location.longitude"] != 0.0) & (df_map["location.latitude"] != 0.0)
]

# setup a multiselect box to filter markers
st_selected_statuses = st.multiselect( # [ST2]
    "Filter skyscrapers by status",
    options = ["completed", "incomplete", "planned", "topped out", "demolished"],
    default = ["completed", "incomplete", "topped out"]
)

# need to relate selected options back to actual statuses
status_mapping = { # [PY5]
    "completed": ["completed"],
    "incomplete": ["on hold", "under construction", "never completed"],
    "planned": ["vision", "proposed"],
    "topped out": ["architecturally topped out", "structurally topped out"],
    "demolished": ["demolished"]
}

status_to_show = [status for selected_status in st_selected_statuses for status in status_mapping[selected_status]] # [PY4]
if st_selected_statuses:
    df_map = df_map[df_map["status.current"].isin(status_to_show)]
    
    # just pass an empty dataframe so that it skips the markers
    if df_map.empty:
        df_map = pd.DataFrame()
else:
    df_map = pd.DataFrame()

# render the initial map
map_center = [df_map['location.latitude'].mean() if not df_map.empty else 0, 
              df_map['location.longitude'].mean() if not df_map.empty else 0]
m = fm.Map(location=map_center, zoom_start=3, tiles='CartoDB dark_matter')

# we only want to add markers if and only if there is things to mark
if not df_map.empty:
    for _, row in df_map.iterrows(): # [DA8]
        fm.CircleMarker(
            location=[row['location.latitude'], row['location.longitude']],
            radius=2,
            color=row['color'],
            fill=True,
            fill_color=row['color'],
            fill_opacity=0.6
        ).add_to(m)

# display the map
st.components.v1.html(m._repr_html_(), width=700, height=500) # [MAP]

# List out skyscrapers by city, then lets show other info
st.markdown("<div class='title'>Skyscrapers by city</div>", unsafe_allow_html=True)
city_names = df["location.city"].dropna().unique()
frequency_by_city = df["location.city"].value_counts() # this method returns a series with city name as keys and frequency as values
city_names = [f"{city} ({frequency_by_city[city]})" for city in city_names] # [PY4]
city_names.sort()
st.markdown("<div class='regular-text'>Tell me about skyscrapers in...</div>", unsafe_allow_html=True)
st_selected_city = st.selectbox(# [ST1]
    " ",
    city_names,
      index=city_names.index(
        f"New York City ({frequency_by_city['New York City']})"
        ))
# filter by selected city
df_selected_city = df[df["location.city"] == st_selected_city.rsplit(" (", 1)[0].rstrip()] # [DA4]
# only show the relevant columns
df_selected_city = df_selected_city[
    [
        "name",
        "statistics.height",
        "statistics.rank",
        "status.completed.year",
        "status.current"
    ]
]
# rename columns to be more legible
df_selected_city = df_selected_city.rename(columns={
    "name": "Name",
    "statistics.height": "Height (meters)",
    "statistics.rank": "Rank",
    "status.completed.year": "Year completed",
    "status.current": "Current status",
})
# replace instances of year = 0 with 'uncompleted'
# .apply() applies a given function to all columns. since we only need to proc this function once we can use anonymous (python calls it lambda) function
df_selected_city["Year completed"] = df_selected_city["Year completed"].apply(lambda year: "Uncompleted" if year == 0 else str(year)) # [DA1]
# sometimes uncompleted skyscrapers also are un-started. we can figure this out based on the status
# in this case, i want to edit rows instead of columns, so pandas already can do this easily
df_selected_city.loc[ df_selected_city["Current status"] == "vision", "Year completed" ] = "planning"
df_selected_city.loc[ df_selected_city["Current status"] == "proposed", "Year completed" ] = "planning"
# filter this df by skyscraper name
df_selected_city = df_selected_city.sort_values(by="Name") # [DA2]

# finally, put this updated panel on the webpage
st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
st.dataframe(df_selected_city, width=1000)
st.markdown("</div>", unsafe_allow_html=True)


st_selected_city = st_selected_city.rsplit(" (", 1)[0].rstrip()
df_selected_city_sorted = df_selected_city.sort_values("Height (meters)", ascending=False)
top_heights = df_selected_city_sorted.head(24)

hist, axis3 = plt.subplots(figsize = (max(10, len(top_heights) * 0.4), 8)) # [PY1] I use this for all the matplotlib plots. figsize is an optional parameter
axis3.bar(top_heights["Name"], top_heights["Height (meters)"], color="#87CEEB")
axis3.set_ylabel("Height (meters)")
axis3.set_xlabel("Skyscraper Name")
axis3.set_title(f"Top heights of skyscrapers in {st_selected_city}")
plt.xticks(rotation=75) # make the names slanted

st.pyplot(hist)
# [VIZ3]

index_tallest = df_selected_city["Height (meters)"].idxmax() # [DA3]
tallest_name = df.loc[index_tallest, "name"]
tallest_height = df.loc[index_tallest, "statistics.height"]
tallest_rank = df.loc[index_tallest, "statistics.rank"]
tallest_sealevel = df.loc[index_tallest, "statistics.floors above"]
tallest_started = df.loc[index_tallest, "status.started.year"]
tallest_completed = df.loc[index_tallest, "status.completed.year"]
tallest_status = df.loc[index_tallest, "status.current"]

# Define purposes categories
purposes_location = ["museum", "casino", "library", "air traffic control tower", "hotel", "office"]
purposes_other = ["retail", "industrial", "residential", "commercial"]

# Extract purposes based on truth values
location_purposes = [
    purpose for purpose in purposes_location
    if df.loc[index_tallest, f"purposes.{purpose}"]
]
other_purposes = [
    purpose for purpose in purposes_other
    if df.loc[index_tallest, f"purposes.{purpose}"]
]

if st_selected_city:
    summary_str = f"The tallest skyscraper in {st_selected_city} is the '{tallest_name}' standing at {tallest_height:.2f} meters, or {tallest_sealevel} floors above sea level. "

    if tallest_started != 0:
        if tallest_completed != 0:
            summary_str += f"The building began construction in {tallest_started} and was finished {tallest_completed - tallest_started} years later in {tallest_completed}. "

            if location_purposes:
                if len(location_purposes) == 1:
                    summary_str += f"The building serves as a {location_purposes[0]}. "
                else:
                    summary_str += f"The building serves as {', '.join(location_purposes[:-1])}, and {location_purposes[-1]}. "

            if other_purposes:
                if len(other_purposes) == 1:
                    summary_str += f"Additionally, it has {other_purposes[0]} purposes. "
                else:
                    summary_str += f"Additionally, it serves {', '.join(other_purposes[:-1])}, and {other_purposes[-1]} purposes. "
        else:
            summary_str += f"The building has not completed and currently is {tallest_status}. "

            if location_purposes:
                if len(location_purposes) == 1:
                    summary_str += f"It is planned to serve as a {location_purposes[0]}. "
                else:
                    summary_str += f"It is planned to serve as {', '.join(location_purposes[:-1])}, and {location_purposes[-1]}. "

            if other_purposes:
                if len(other_purposes) == 1:
                    summary_str += f"Additionally, it is planned to have {other_purposes[0]} purposes. "
                else:
                    summary_str += f"Additionally, it is planned to serve {', '.join(other_purposes[:-1])}, and {other_purposes[-1]} purposes. "
    elif tallest_status != "completed":
        summary_str = (
            f"The {tallest_name} is currently in the early planning stage, but it is set to be the tallest skyscraper in {st_selected_city} at {tallest_height:.2f} meters, or {tallest_sealevel} floors above sea level. "
            f"However, the {tallest_name} is in the {tallest_status} stage, so it's unsure whether it will live up to the expectations."
        )

    st.markdown("<div class='regular-text'>" + summary_str + "</div>", unsafe_allow_html=True)


# Other charts

# constructions started over time
st.markdown("<div class='title'>Constructions started over time</div>", unsafe_allow_html=True)
bucket_selected = st.slider("Year interval bucekt", 1, 10)# [ST3]

# ignore years without data (0)
df_years = df[ df["status.started.year"] > 0]

# get the lowest year and use it to make a interval for starting year
min_year = df_years["status.started.year"].min()
start_year = st.slider("Set start year", min_year, 2000, min_year)

# assign a bucket for plotting purposes (bucket-yr intervals)
df_years["bucket"] = (df_years["status.started.year"] // bucket_selected) * bucket_selected

# expunge everything prior to start year
df_years_filtered = df_years[df_years["status.started.year"] >= start_year]
# group data by bucket and get frequencies
bucketed_data = df_years_filtered.groupby("bucket").size()

# matplotlib scatter plot setup
scatter, axis1 = plt.subplots() # [PY2] touple
axis1.scatter(bucketed_data.index, bucketed_data.values, color="blue")
axis1.set_title("Number of skyscrapers built/attempted over time")
axis1.set_xlabel(f"Year ({bucket_selected}yr intervals)")
axis1.set_ylabel("Number of constructions")


st.pyplot(scatter) # [VIZ2]

# statuses of buildings
st.markdown("<div class='title'>Skyscrapers by status</div>", unsafe_allow_html=True)
status_counts = {
    'completed': 0,
    'on hold': 0,
    'demolished': 0,
    'under construction': 0,
    'topped out': 0
}

# tally up each status for frequencies to plot
for status in df['status.current']:
    if status == 'completed':
        status_counts['completed'] += 1
    elif status == 'on hold':
        status_counts['on hold'] += 1
    elif status == 'demolished':
        status_counts['demolished'] += 1
    elif status == 'under construction':
        status_counts['under construction'] += 1
    elif status == 'architecturally topped out':
        status_counts['topped out'] += 1
    elif status == 'structurally topped out':
        status_counts['topped out'] += 1

# setup labels and values
status_labels = list(status_counts.keys())
status_values = list(status_counts.values())
colors = ['green', 'orange', 'black', 'blue', 'yellow']

# matplotlib horizontal barchart setup
barh, axis2 = plt.subplots()
axis2.barh(status_labels, status_values, color=colors)
axis2.set_xlabel('Number of Skyscrapers')
axis2.set_title('Skyscraper Status Distribution')

# broadcast on streamlit
st.pyplot(barh) # [VIZ1]
