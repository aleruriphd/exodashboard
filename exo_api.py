import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests
import streamlit as st
import altair as alt
import os
import datetime
import numpy as np
from io import BytesIO

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
@st.cache_data
def download_table():

    placeholder1 = st.empty()
    initial_message = "The latest version of the NASA's exoplanet archive is being downloaded as a table with today's date does not exist in this server."
    st.write(initial_message)
    placeholder1.text("The latest version of the NASA's exoplanet archive is being downloaded as a table with today's date does not exist in this server.")
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+ps&format=csv"

    # Make a GET request to fetch the content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # If successful, write the content to a CSV file
        with open("full_table_nasa_url.csv", "wb") as file:
            file.write(response.content)
        placeholder1.text("Success! Retrieved full_table_nasa_url.csv")
        initial_message = "Success! Retrieved full_table_nasa_url.csv"
        st.write(initial_message)
        st.write("")
    else:
        placeholder1.text(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")
        initial_message = f"Failed to retrieve data. HTTP Status Code: {response.status_code}"
        st.write(initial_message)

    placeholder1.empty()

@st.cache_data
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
    mod_time = os.path.getmtime(file_path)
    # Convert the modification time to a datetime object
    mod_date = datetime.datetime.fromtimestamp(mod_time)


def use_latest_table():
    file_path = 'latest_full_table_nasa_url.csv'
    

#Converting the table to a dataframe
@st.cache_data    
def converting_table_to_df(csv_file):
    #st.write("Converting downloaded table to a dataframe")
    full_table_df = pd.read_csv(csv_file)


    table = full_table_df[full_table_df['default_flag'] > 0]

    table.reset_index(drop=True, inplace=True)
    table.index +=1

    # Export the DataFrame to a CSV file
    table.to_csv('confirmed_exoplanets_data.csv', index_label='ID')
    st.write("")

    return(table)

#st.button("Download the latest table from the NASA's website", on_click = download_table())
#st.button("use the latest table in this server with date: " + str(mod_date.date()), on_click = use_latest_table())

table_confirmed_planets_df = converting_table_to_df(file_path)

alt.themes.enable("dark")

st.header('', divider='blue')
st.write("Source: [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/index.html)")
st.write("By Alejandro Ruiz Rivera, PhD.")
st.write("[Medium Profile](https://medium.com/@ruizrivera.alejandro)")
st.write("[Linkedin Profile](https://www.linkedin.com/in/alejandro-ruiz-ph-d/)")
st.write("[Google Scholar Profile](https://scholar.google.com.au/citations?user=zi4G4pUAAAAJ&hl=en)")
st.write("[A Story of More Than 5000 Worlds](https://books2read.com/more-than-5000-worlds)")
st.write("[Una historia de mas de 5000 mundos](https://books2read.com/mas-de-5000-mundos)")
#Display the book covers images
book_covers = 'images/caratulas libros.png'
st.image(book_covers, width=300)
st.header('', divider='blue')


if tab1:
    with tab1:
        col = st.columns((2.5, 2.5, 2.5), gap='medium')
        #with st.sidebar:
        with col[0]:

            @st.cache_data    
            def categorize_by_size_and_mass_vectorized(radius, mass):
                conditions = [
                    (radius > 4.5) | (mass >= 159),
                    (radius > 2.1) & (radius <= 4.5) | ((mass >= 10) & (mass < 159)),
                    (radius > 1.0) & (radius <= 2.1) | ((mass >= 1) & (mass < 10)),
                    (radius > 0.1) & (radius <= 1.0) | ((mass > 0.1) & (mass < 1)),
                ]
                choices = ['gas_giants', 'ice_giants', 'super_earths', 'terrestrial']
                return np.select(conditions, choices, default='unclassified')
            
            # Add 'All' option to the method list
            st.write("Using the NASA's exoplanet archive table with date: " + str(mod_date.date())+ ".")
            method_list = ['All'] + list(table_confirmed_planets_df.discoverymethod.unique())[::-1]
            selected_method = st.selectbox('Select an exoplanet detection method', method_list, index=0) # Default to 'All'

            # Apply the function to each row of the DataFrame
            table_confirmed_planets_df['category'] = categorize_by_size_and_mass_vectorized(table_confirmed_planets_df['pl_rade'], table_confirmed_planets_df['pl_bmasse'])
            category_counts_all = table_confirmed_planets_df['category'].value_counts()

            if selected_method == 'All':
                df_selected_method = table_confirmed_planets_df
                
            else:
                df_selected_method = table_confirmed_planets_df[table_confirmed_planets_df.discoverymethod == selected_method]
                #print(df_selected_method)

            
            display_image(selected_method)

            st.text('In Earth masses and Earth radii')
            st.header('', divider='blue')
            st.text('Gas Giants:   Radius > 4.5 or Mass >= 159')
        
            st.text('Ice Giants:   2.1 < Radius <= 4.5 or 10  <= Mass <159')

            st.text('Super Earths: 1.0 < Radius <= 2.1 or 1 <= Mass <10')

            st.text('Terrestrial:  0.1 < Radius <= 1.0 or 0.1 < Mass < 1')


        # Count the number of instances in each category
        category_counts = df_selected_method['category'].value_counts()


        # Pie chart, where the slices will be ordered and plotted counter-clockwise:
        categories = category_counts.index.to_list()

        if 'unclassified' in categories:
            categories.remove('unclassified')  # Remove 'unclassified' if it exists
            categories.append('unclassified')  # Append 'unclassified' to the end of the list

        counts = category_counts.values
        total_counts = sum(counts)

        #col = st.columns((2.0, 3.0), gap='medium')

        with col[1]:  #Will show the counts for each category
            st.title(selected_method)
            st.header('', divider='rainbow')

            cols_in_col_1 = st.columns((2.0, 3.0), gap='medium')

            def download_csv_detection(csv_detection_method):
                    # Export the DataFrame to a CSV file
                    return csv_detection_method.to_csv(index_label='ID').encode('utf-8')

            csv_to_download = download_csv_detection (df_selected_method)



            with cols_in_col_1[0]:
                for i in range(len(categories)):
                    st.metric(label=categories[i], value=counts[i], label_visibility="visible")
   
            
                st.metric(label='Total', value = total_counts, label_visibility="visible")

            with cols_in_col_1[1]:

                st.download_button(label="Download the csv file for this detection method", data = csv_to_download, file_name= selected_method + "_confirmed_exoplanets.csv", mime="text/csv",)

                #st.button("Download the csv file for this detection method", on_click = download_csv_detection(selected_method, df_selected_method))





        with col[2]:  #The pie chart for the categories will be presented

            #We remove the 'unclassified' category so it is not shown in the pie chart

            if 'unclassified' in categories:
                index_to_remove = categories.index('unclassified')

                # Remove the category and its corresponding count
                del categories[index_to_remove]
                counts = [count for i, count in enumerate(counts) if i != index_to_remove] 

                st.markdown('')

            st.write("*Unclassified exoplanets are not included in the pie chart")
            fig1, ax1 = plt.subplots()

            if selected_method =="All":
                plt.title("Categories of all detected exoplanets")

            else:
                plt.title("Categories of exoplanets detected using the " + selected_method + " method")
            ax1.pie(counts, labels=categories, autopct='%1.1f%%',shadow=True, startangle=90, radius = 2)
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            st.pyplot(fig1)

            # Save the plot to a BytesIO object
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)

            #user can download the generated pie chart
            st.download_button(label="Download this pie chart", data = buf, file_name= selected_method + "_pie_chart.png", mime="image/png",)

# Convert all values in the 'pl_name' column to lowercase
table_confirmed_planets_df['pl_name'] = table_confirmed_planets_df['pl_name'].str.lower()
column_list = list(table_confirmed_planets_df.columns)
# Export the DataFrame to a CSV file
table_confirmed_planets_df.to_csv('confirmed_exoplanets_data_categories.csv', index_label='ID')

if tab2:
    #Initializing the name of the exoplanet so it is not empty
    exoplanet_name = 'Kepler-167 e'
    exoplanet_name = exoplanet_name.lower()

    with tab2: 

        exoplanet_name =  st.text_input("Enter the name of the exoplanet", key="exoname",).lower()
        #exoplanet_name =  'HAT-P-21 b'
        #exoplanet_name = exoplanet_name.lower()

        #@st.cache_data
        def return_planet_parameter(name_of_planet,table, parameter):

            if parameter=="defaultflag":
                default_flag = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'default_flag'].values[0] 
                parameter_value = default_flag

            if parameter=='planet_type':
                pl_type = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'category'].values[0]  
                parameter_value = pl_type  
            
        
            elif parameter=='planet_size':
                planet_radius = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'pl_rade'].values[0]
                parameter_value = planet_radius

            elif parameter=='planet_mass_in_earths':
                pl_mass_earth = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'pl_bmasse'].values[0]
                parameter_value = pl_mass_earth

            elif parameter=='planet_mass_in_jupiters':
                pl_mass_jupiter = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'pl_bmassj'].values[0]
                parameter_value = pl_mass_jupiter

            elif parameter=='planet_semimajor':
                pl_semi_major_au = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'pl_orbsmax'].values[0]
                parameter_value = pl_semi_major_au

            elif parameter=='planet_eq_temp':
                pl_eq_temp = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'pl_eqt'].values[0]   
                parameter_value = pl_eq_temp     

            elif parameter=='star_name':
                host_name = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'hostname'].values[0] 
                parameter_value = host_name

            elif parameter=='star_spec_type':
                host_spect_type = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'st_spectype'].values[0] 
                parameter_value = host_spect_type

            elif parameter=='star_eff_temp':
                host_effect_temp = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == name_of_planet, 'st_teff'].values[0] 
                parameter_value = host_effect_temp

            return(parameter_value)


        if exoplanet_name:
            if table_confirmed_planets_df['pl_name'].isin([exoplanet_name]).any():

                pl_disc_method = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, 'discoverymethod'].values[0]  
                st.title(exoplanet_name)
                st.write('Detection method:', pl_disc_method)
                st.header('', divider='blue')



                table = table_confirmed_planets_df
                first_row_col= st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')

                with first_row_col[0]:
                    st.text_area("Type:", return_planet_parameter(exoplanet_name,table,'planet_type'), height=5, disabled=True)
        
                with first_row_col[1]:
                    st.text_area("Radius in Earth radii:", return_planet_parameter(exoplanet_name,table,'planet_size'), height=5, disabled=True)

                with first_row_col[2]:
                    st.text_area("Mass in Earth Masses:", return_planet_parameter(exoplanet_name,table,'planet_mass_in_earths'), height=5, disabled=True)

                with first_row_col[3]:
                    st.text_area("Mass in Jupiter Masses:", return_planet_parameter(exoplanet_name,table,'planet_mass_in_jupiters'), height=5, disabled=True)

                second_row_col = st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')

                with second_row_col[0]:
                    st.text_area("Dist. from its parent star (AU):", return_planet_parameter(exoplanet_name,table,'planet_semimajor'), height=5, disabled=True)

                with second_row_col[1]:
                    st.text_area("Equilibrium temperature (Kelvin):", return_planet_parameter(exoplanet_name,table,'planet_eq_temp'), height=5, disabled=True)    

                with second_row_col[2]:
                    st.text_area("Parent star name:", return_planet_parameter(exoplanet_name,table,'star_name'), height=5, disabled=True)

                with second_row_col[3]:
                    st.text_area("Parent star type:", return_planet_parameter(exoplanet_name,table,'star_spec_type'), height=5, disabled=True)


                third_row_col = st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')

                with third_row_col[0]:
                    st.text_area("Eff. Temp of parent star:", return_planet_parameter(exoplanet_name,table,'star_eff_temp'), height=5, disabled=True)

                # Use st.selectbox to let the user select a parameter
                selected_column = st.selectbox('Custom user parameter', column_list, index=11)  # Default to the first column in the list
                custom = table_confirmed_planets_df.loc[table_confirmed_planets_df['pl_name'] == exoplanet_name, selected_column].values[0] 

                fourth_row_col = st.columns((1.0, 1.0, 1.0, 1.0), gap='medium')
                with fourth_row_col[0]:
                    st.text_area(selected_column, custom, height=10, disabled=True)


            else:
                # The name is not present in the DataFrame
                st.title(exoplanet_name)
                st.header('', divider='blue')
                st.write(f"The exoplanet '{exoplanet_name}' was not found in the database.")


        else:
            st.write("")

   
if tab3:

    with tab3:

        categories_tab3 = category_counts_all.index.to_list()

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

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        #user can download the generated scatter chart
        st.download_button(label="Download this scatter chart", data = buf, file_name= selected_type + "_scatter_chart.png", mime="image/png",)        




