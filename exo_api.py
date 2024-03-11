import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from ipywidgets import interact
import csv
import requests
import streamlit as st
#from streamlit_jupyter import StreamlitPatcher, tqdm
#StreamlitPatcher().jupyter()  # register streamlit with jupyter-compatible wrappers
import altair as alt
import plotly.express as px
import os
import datetime

st.set_page_config(
    page_title="Exoplanet Population Dashboard",
    page_icon="🔮",   
    layout="wide",
    initial_sidebar_state="expanded")

tab1, tab2, tab3 = st.tabs(["Exoplanet Population stats", "Exoplanet Data", "Mass vs Semi-major axis scatter plots"])


metric_style = """
<div style="
    border-radius: 10px;
    background-color: blue;
    color: white;
    padding: 10px;
    text-align: center;
    display: inline-block;
    margin: 10px;">
    <h2 style="margin:0;">Total</h2>
    <h1 style="margin:0;">{}</h1>
</div>
"""

def download_table():
    print("Attempting to download the latest version of the NASA's exoplanet archive")
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+ps&format=csv"

    # Make a GET request to fetch the content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # If successful, write the content to a CSV file
        with open("full_table_nasa_url.csv", "wb") as file:
            file.write(response.content)
        print("Success! Retrieved full_table_nasa_url.csv")
    else:
        print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")

def display_image(value):

    name_of_pic = 'images/' + value + '.png'
    st.image(name_of_pic)

# File path
file_path = 'full_table_nasa_url.csv'

# Check if the file exists
if os.path.exists(file_path):
    # Get the last modification time of the file
    mod_time = os.path.getmtime(file_path)
    # Convert the modification time to a datetime object
    mod_date = datetime.datetime.fromtimestamp(mod_time)
    
    # Get today's date
    today = datetime.datetime.today()
    
    # Compare the modification date and today's date (ignoring the time part)
    if mod_date.date() == today.date():
        print("The table exists and has today's date.")

    else:
        print("The table exists and but it is outdated.")
        download_table()
    
else:
    download_table() 

#Converting the table to a dataframe
full_table_df = pd.read_csv('full_table_nasa_url.csv')


table_confirmed_planets_df = full_table_df[full_table_df['default_flag'] > 0]

table_confirmed_planets_df.reset_index(drop=True, inplace=True)
table_confirmed_planets_df.index +=1

# Export the DataFrame to a CSV file
table_confirmed_planets_df.to_csv('confirmed_exoplanets_data.csv', index_label='ID')



alt.themes.enable("dark")

if tab1:
    with tab1:
        col = st.columns((2.5, 2.5, 2.5), gap='medium')
        #with st.sidebar:
        with col[0]:
            #st.title('🔮 Exoplanet Population Dashboard')
            
            # Add 'All' option to the method list
            method_list = ['All'] + list(table_confirmed_planets_df.discoverymethod.unique())[::-1]
            selected_method = st.selectbox('Select an exoplanet detection method', method_list, index=0) # Default to 'All'

            if selected_method == 'All':
                df_selected_method = table_confirmed_planets_df
            else:
                df_selected_method = table_confirmed_planets_df[table_confirmed_planets_df.discoverymethod == selected_method]

            

            
            display_image(selected_method)

            st.text('In Earth masses and Earth radii')
            st.header('', divider='blue')
            st.text('Gas Giants:   Radius > 4.5 or Mass >= 159')
        
            st.text('Ice Giants:   2.1 < Radius <= 4.5 or 10  <= Mass <159')

            st.text('Super Earths: 1.0 < Radius <= 2.1 or 1 <= Mass <10')

            st.text('Terrestrial:  0.1 < Radius <= 1.0 or 0.1 < Mass < 1')

            
        def categorize_by_size_and_mass(radius, mass):
            if radius > 4.5 or mass >= 159:
                return 'gas_giants'
            elif 2.1 < radius <= 4.5 or 10 <= mass <159:
                return 'ice_giants'
            elif 1.0 < radius <= 2.1 or 1 <= mass <10:
                return 'super_earths'
            elif 0.1 < radius <= 1.0 or 0.1 < mass < 1:
                return 'terrestrial'
            else:
                return 'unclassified'  # For values that don't fit in any bucket
            
        # Apply the function to each row of the DataFrame
        # Note: axis=1 specifies that the function should be applied to each row instead of each column
        table_confirmed_planets_df['category'] = df_selected_method.apply(lambda row: categorize_by_size_and_mass(row['pl_rade'], row['pl_bmasse']), axis=1)



        # Count the number of instances in each category
        category_counts = table_confirmed_planets_df['category'].value_counts()

        # Display the counts
        print(category_counts)

        # Pie chart, where the slices will be ordered and plotted counter-clockwise:
        categories = category_counts.index.to_list()

        if 'unclassified' in categories:
            categories.remove('unclassified')  # Remove 'unclassified' if it exists
            categories.append('unclassified')  # Append 'unclassified' to the end of the list

        counts = category_counts.values
        total_counts = sum(counts)

        #col = st.columns((2.0, 3.0), gap='medium')

        with col[1]:
            st.title(selected_method)
            st.header('', divider='rainbow')

            for i in range(len(categories)):
                st.metric(label=categories[i], value=counts[i], label_visibility="visible")
                #st.markdown(metric_style.format(categories[i]), unsafe_allow_html=True)

            #st.markdown(metric_style.format(total_counts), unsafe_allow_html=True)
            st.header('', divider='blue')    
            st.metric(label='Total', value = total_counts, label_visibility="visible")


        if 'unclassified' in categories:
            index_to_remove = categories.index('unclassified')

            # Remove the category and its corresponding count
            del categories[index_to_remove]
            counts = [count for i, count in enumerate(counts) if i != index_to_remove] 


            


        with col[2]:

            st.markdown('')

            fig1, ax1 = plt.subplots()
            ax1.pie(counts, labels=categories, autopct='%1.1f%%',shadow=True, startangle=90, radius = 2)
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            st.pyplot(fig1)

            #exoplanet_name =  'GJ 667 C b'
            #pl_type = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'category'].values[0]  
            #print(pl_type)

# Convert all values in the 'pl_name' column to lowercase
table_confirmed_planets_df['pl_name'] = table_confirmed_planets_df['pl_name'].str.lower()
column_list = list(table_confirmed_planets_df.columns)
# Export the DataFrame to a CSV file
table_confirmed_planets_df.to_csv('confirmed_exoplanets_data_categories.csv', index_label='ID')

if tab2:

    with tab2: 

        exoplanet_name =  st.text_input("Enter the name of the exoplanet", key="exoname",).lower()
        #exoplanet_name =  'HAT-P-21 b'
        #exoplanet_name = exoplanet_name.lower()



        if exoplanet_name:
            if table_confirmed_planets_df['pl_name'].isin([exoplanet_name]).any():

                pl_disc_method = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'discoverymethod'].values[0]  
                st.title(exoplanet_name)
                st.write('Detection method:', pl_disc_method)
                st.header('', divider='blue')

                pl_type = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'category'].values[0]    
                print(pl_type)    
                
                planet_radius = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'pl_rade'].values[0]

                pl_mass_earth = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'pl_bmasse'].values[0]

                pl_mass_jupiter = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'pl_bmassj'].values[0]

                pl_semi_major_au = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'pl_orbsmax'].values[0]

                pl_eq_temp = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'pl_eqt'].values[0]        

                host_name = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'hostname'].values[0] 

                host_spect_type = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'st_spectype'].values[0] 

                host_spect_type = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'st_spectype'].values[0] 

                host_effect_temp = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'st_teff'].values[0] 


                first_row_col= st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')

                with first_row_col[0]:
                    st.text_area("Type:", pl_type, height=5, disabled=True)
        
                with first_row_col[1]:
                    st.text_area("Radius in Earth radii:", planet_radius , height=5, disabled=True)

                with first_row_col[2]:
                    st.text_area("Mass in Earth Masses:", pl_mass_earth, height=5, disabled=True)

                with first_row_col[3]:
                    st.text_area("Mass in Jupiter Masses:", pl_mass_jupiter, height=5, disabled=True)



                second_row_col = st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')

                with second_row_col[0]:
                    st.text_area("Dist. from its parent star (AU):", pl_semi_major_au, height=5, disabled=True)

                with second_row_col[1]:
                    st.text_area("Equilibrium temperature (Kelvin):", pl_eq_temp, height=5, disabled=True)    

                with second_row_col[2]:
                    st.text_area("Parent star name:", host_name, height=5, disabled=True)

                with second_row_col[3]:
                    st.text_area("Parent star type:", host_spect_type, height=5, disabled=True)


                third_row_col = st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')

                with third_row_col[0]:
                    st.text_area("Eff. Temp of parent star:", host_effect_temp, height=5, disabled=True)

                # Use st.selectbox to let the user select a parameter
                selected_column = st.selectbox('Select a parameter', column_list, index=11)  # Default to the first column in the list
                custom = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, selected_column].values[0] 

                fourth_row_col = st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')
                with fourth_row_col[0]:
                    st.text_area(selected_column, custom, height=5, disabled=True)


            else:
                # The name is not present in the DataFrame
                st.title(exoplanet_name)
                st.header('', divider='blue')
                st.write(f"The exoplanet '{exoplanet_name}' was not found in the database.")


        else:
            st.write("")

   
if tab3:

    with tab3:

        categories_tab3 = category_counts.index.to_list()

        if 'unclassified' in categories_tab3:
            categories_tab3.remove('unclassified')  # Remove 'unclassified' if it exists

        selected_type = st.selectbox('Select a parameter', categories_tab3, index=0)  # Default to the first column in the list


        # Create a boolean mask where True corresponds to rows with selected type category
        mask = table_confirmed_planets_df['category'] == selected_type

        # Use the mask to filter the DataFrame, keeping only rows where the category is the selected type
        type_of_planets_df = table_confirmed_planets_df[mask]

        # Create a scatter plot
        st.write('Scatter plot:', selected_type)
        st.header('', divider='blue')
        plt.figure(figsize=(10, 6))  # Optional: Define the size of the figure
        plt.scatter(type_of_planets_df['pl_orbsmax'], type_of_planets_df['pl_bmasse'])
        plt.title(selected_type)
        plt.xlabel('Maximum Orbital Distance (AU)')
        plt.ylabel('Mass (Earth Masses)')

        # Display the plot in Streamlit
        st.pyplot(plt)




