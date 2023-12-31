import streamlit as st
import pandas as pd
import io
from io import BytesIO
import plotly.express as px
import plotly.graph_objs as go
import base64  # Import the base64 module

# Set page configuration
st.set_page_config(page_title="END OF SEASON")

# Create a sidebar with a dropdown to select the number of clans
st.sidebar.title("Select Number of Clans")
num_clans = st.sidebar.selectbox("Number of Clans", [2, 3, 4, 5, 6, 7, 8])

# Create a sidebar with a single file uploader for all files
st.sidebar.title("Upload Files")
all_files_upload = st.sidebar.file_uploader("Upload All Files", type=["xlsx"], accept_multiple_files=True)
sort_order = st.selectbox("Type", ["War Stars", "Top Member", "Donations", "EOS Trophies","Capital Gold Contributed","Capital Gold Looted","Main Base","Builder Base","Capital","All"])

# Process uploaded files
if all_files_upload :
    # Read and process the uploaded files
    war_file= []
    season_file=[]

    for file_upload in all_files_upload:
        data = pd.read_excel(file_upload, engine="openpyxl")
        if "Total Stars" in data.columns:
            war_file.append(data)
        elif "Total Donated" in data.columns:
            season_file.append(data)

    # Concatenate the DataFrames only if they are not empty
    war_df = pd.concat(war_file, ignore_index=True) if war_file else pd.DataFrame()
    season_df = pd.concat(season_file, ignore_index=True) if season_file else pd.DataFrame()

    if len(all_files_upload) == num_clans * 2 and not war_df.empty and not season_df.empty:
        def preprocess_data(wars, season):
            # Merge wars and season data
            clan = wars.merge(season, on="Name", how="outer")

            clan.drop(columns={'Def Stars', 'Avg. Def Stars',
            'Total Def Dest', 'Avg. Def Dest', 'Tag_y','War-Stars Gained',
            'CWL-Stars Gained', 'Gold Looted', 'Elixir Lotted', 'Dark Elixir Looted',
            'Clan Games','Tag_x','Discord',"Town Hall_x","Town Hall_y"}, inplace=True)
            clan.rename(columns={"Total Attacks_x":"Total War Attacks", 'Total Attacks_y':"Attacks in a Season",'Month_y':"Month"}, inplace=True)
            clan['Total War Attacks'].fillna(clan['Total War Attacks'].min(), inplace=True)
            clan['Total Stars'].fillna(clan['Total Stars'].min(), inplace=True)
            clan['True Stars'].fillna(clan['True Stars'].min(), inplace=True)
            clan['Avg. True Stars'].fillna(clan['Avg. True Stars'].min(), inplace=True)
            clan['Avg. Stars'].fillna(clan['Avg. Stars'].min(), inplace=True)
            clan['Total Dest'].fillna(clan['Total Dest'].min(), inplace=True)
            clan['Avg. Dest'].fillna(clan['Avg. Dest'].min(), inplace=True)
            clan['Two Stars'].fillna(clan['Two Stars'].min(), inplace=True)
            clan['One Stars'].fillna(clan['One Stars'].min(), inplace=True)
            clan['Zero Stars'].fillna(clan['Zero Stars'].min(), inplace=True)
            clan['Three Stars'].fillna(clan['Three Stars'].min(), inplace=True)
            clan['Missed'].fillna(clan['Missed'].min(), inplace=True)
            clan['Total Donated'].fillna(0, inplace=True)
            clan['Total Received'].fillna(0, inplace=True)
            clan['Attacks in a Season'].fillna(0, inplace=True)
            clan['Versus Attacks'].fillna(0, inplace=True)
            clan['Trophies Gained'].fillna(0, inplace=True)
            clan['Season-End Trophies'].fillna(clan['Season-End Trophies'].min(), inplace=True)
            clan['Versus-Trophies Gained'].fillna(0, inplace=True)
            clan['Capital Gold Looted'].fillna(0, inplace=True)
            clan['Capital Gold Contributed'].fillna(0, inplace=True)
            clan['Activity Score'].fillna(clan['Activity Score'].min(), inplace=True)

            def war_score_func(value):
                ul = clan['Total Stars'].quantile(0.75)
                ll = clan['Total Stars'].quantile(0.25)
                war_score = 0.6 * (value - ll) * 10.0 / (ul - ll)
                return war_score

            clan["War Score"] = clan["Total Stars"].apply(war_score_func)

            def donation_score_func(value):
                ul = clan['Total Donated'].quantile(0.75)
                ll = clan['Total Donated'].quantile(0.25)
                donation_score = 0.3 * (value - ll) * 10.0 / (ul - ll)
                return donation_score

            clan["Donation Score"] = clan["Total Donated"].apply(donation_score_func)

            def activity_score_func(value):
                ul = clan['Activity Score'].quantile(0.75)
                ll = clan['Activity Score'].quantile(0.25)
                final_activity_score = 0.1 * (value - ll) * 10.0 / (ul - ll)
                return final_activity_score

            clan["Final Activity Score"] = clan["Activity Score"].apply(activity_score_func)

            def missed_attack_function(value):
                missed_attack_score = (value) ** 2
                return missed_attack_score

            clan["Missed Attack Score"] = clan["Missed"].apply(missed_attack_function)
            clan = clan.assign(season_score=clan['War Score'] + clan['Donation Score'] + clan['Final Activity Score'] - clan['Missed Attack Score'])

            return clan

        # Preprocess data
        final_merged_data = preprocess_data(war_df, season_df)
        # Define sorting functions based on selected order
        sort_functions = {
            "War Stars": "Total Stars",
            "Top Member": "season_score",
            "Donations": "Total Donated",
            "EOS Trophies": "Season-End Trophies",
            "Capital Gold Contributed":"Capital Gold Contributed",
            "Capital Gold Looted":"Capital Gold Looted"
        }
        titles = {
            "War Stars": "War Monger",
            "Top Member": "Top Member",
            "Donations": "Donation Machine",
            "EOS Trophies": "Legendary Attacker",
            "Capital Gold Contributed":"Capital Gold Contributed",
            "Capital Gold Looted":"Capital Gold Looted",
            "All": "Best Players ",
            "Main Base":"Main Base",
            "Builder Base":"Builder Base",
            "Capital":"Capital"
        }
        sub_data=final_merged_data
        final_merged_data.drop(columns={"Activity Score","Missed Attack Score"},inplace=True)
        final_merged_data=final_merged_data.reset_index(drop=True)
        num_players_to_display = st.number_input("Number of Players to Display", min_value=1, max_value=len(final_merged_data), value=10)
        if sort_order=="Main Base":
            final_merged_data=final_merged_data.sort_values(by="season_score",ascending=True)
            sub_data=sub_data[['Name',"Clan","Total War Attacks","Total Stars","Three Stars","Avg. Stars","Total Dest","Total Donated","Season-End Trophies","season_score"]]
            display_df=sub_data.sort_values(by="season_score",ascending=False).head(num_players_to_display)
            fig=go.Figure()
            fig=px.bar(display_df,x=display_df.Name,y='season_score',color="season_score",text='season_score',title='Top Performers',height=500,width=700,color_continuous_scale='YlOrRd')
            fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')
        if sort_order=="Builder Base":
            final_merged_data=final_merged_data.sort_values(by="Versus-Trophies Gained",ascending=True)
            sub_data=sub_data[["Name","Clan","Versus Attacks","Versus-Trophies Gained"]]
            display_df=sub_data.sort_values(by="Versus-Trophies Gained",ascending=False).head(num_players_to_display)
            fig=go.Figure()
            fig=px.bar(display_df,x=display_df.Name,y='Versus-Trophies Gained',color="Versus-Trophies Gained",text='Versus-Trophies Gained',title='Versus Trophies Gained',height=500,width=700,color_continuous_scale='YlOrRd')
            fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')
        if sort_order=="Capital":
            final_merged_data=final_merged_data.sort_values(by="Capital Gold Contributed",ascending=True)
            sub_data=sub_data[["Name","Clan",'Capital Gold Looted','Capital Gold Contributed']]
            display_df=sub_data.sort_values(by="Capital Gold Contributed",ascending=False).head(num_players_to_display)
            fig=go.Figure()
            fig=px.bar(display_df,x=display_df.Name,y='Capital Gold Contributed',color="Capital Gold Contributed",text='Capital Gold Contributed',title="Most Capital Gold Contributed",height=500,width=700,color_continuous_scale='YlOrRd')
            fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')
        # Sort the dataframe based on the selected order
        if sort_order in sort_functions:
            final_merged_data = final_merged_data.sort_values(by=sort_functions[sort_order], ascending=False)
            display_df= final_merged_data.head(num_players_to_display)


            if sort_order=="War Stars":
                display_df=display_df[['Name','Clan',"Total War Attacks", 'Total Stars', 'Avg. Stars',
       'True Stars', 'Avg. True Stars', 'Total Dest', 'Avg. Dest',
       'Three Stars', 'Two Stars', 'One Stars', 'Zero Stars', 'Missed',"War Score"]]
                fig = px.bar(display_df, x="Name",y="Total Stars",color="Total Stars",text="Total Stars",hover_data=["Total War Attacks","Total Stars","Three Stars","Avg. Stars","Total Dest"],hover_name="Name",title="Most War Stars",height=500,width=700,color_continuous_scale='YlOrRd')
                fig.update_traces(texttemplate='%{text:.3s}', textposition='outside')
            if sort_order=="Capital Gold Contributed":
                display_df=display_df[["Name","Clan",'Capital Gold Looted','Capital Gold Contributed']]
                fig=go.Figure()
                fig=px.bar(display_df,x=display_df.Name,y='Capital Gold Contributed',color="Capital Gold Contributed",hover_data=['Capital Gold Looted','Capital Gold Contributed'],hover_name="Name",text='Capital Gold Contributed',title="Most Capital Gold Contributed",height=500,width=700,color_continuous_scale='YlOrRd')
                fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')

            if sort_order=="Capital Gold Looted":
                display_df=display_df[["Name","Clan",'Capital Gold Looted','Capital Gold Contributed']]
                fig=go.Figure()
                fig=px.bar(display_df,x=display_df.Name,y='Capital Gold Looted',color="Capital Gold Looted",hover_data=['Capital Gold Looted','Capital Gold Contributed'],hover_name="Name",text='Capital Gold Looted',title="Most Capital Gold Looted",height=500,width=700,color_continuous_scale='YlOrRd')
                fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')

            if sort_order=="Top Member":
                display_df=display_df[["Name","Clan","Total Stars","Total Donated", "Missed","season_score"]]
                fig=go.Figure()
                fig=px.bar(display_df,x=display_df.Name,y='season_score',color="season_score",text='season_score',hover_data=["Total Stars","Total Donated", "Missed","season_score"],hover_name="Name",title='Top Performers',height=500,width=700,color_continuous_scale='YlOrRd')
                fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')

            if sort_order=="Donations":
                display_df=display_df[["Name","Clan",'Total Donated', 'Total Received','Donation Score']]
                fig=go.Figure()
                fig=px.bar(display_df,x=display_df.Name,y='Total Donated',color="Total Donated",text='Total Donated',hover_data=['Total Donated', 'Total Received','Donation Score'],hover_name="Name",title="Most Donations",height=500,width=700,color_continuous_scale='YlOrRd')
                fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')

            if sort_order=="EOS Trophies":
                display_df=display_df[["Name","Clan","Season-End Trophies","Total Stars",'Total Donated']]
                fig=go.Figure()
                fig=px.bar(display_df,x=display_df.Name,y='Season-End Trophies',color="Season-End Trophies",text='Season-End Trophies',title="Maximum Trophies",height=500,width=700,color_continuous_scale='YlOrRd')
                fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')


        if sort_order=="All":
            display_df=final_merged_data.sort_values(by="season_score",ascending=False).head(num_players_to_display)
            fig=go.Figure()
            fig=px.bar(display_df,x=display_df.Name,y='season_score',color="season_score",text='season_score',hover_name="Name",title='Best Performers',height=500,width=700,color_continuous_scale='YlOrRd')
            fig.update_traces(texttemplate='%{text:.3s}',textposition='outside')
            
        # Display the merged preprocessed data
        st.title("Final Data")
        st.write(display_df.reset_index(drop=True))
        st.title(titles[sort_order])
        st.plotly_chart(fig)
        if st.button("Download DataFrame as Excel"):
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                final_merged_data.to_excel(writer, sheet_name="Sheet1", index=False)

    # Set up the download link using an HTML anchor tag
            excel_buffer.seek(0)
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(excel_buffer.read()).decode()}" download="final_merged_data.xlsx">Click here to download the Excel file</a>'
            st.markdown(href, unsafe_allow_html=True)

        columns_to_max = ["Total Stars", "Total Donated", "Season-End Trophies", "Attacks in a Season","season_score","Capital Gold Contributed","Capital Gold Looted"]

        # Initialize an empty list to store the data
        data_list = []
        # Loop through the columns and find the name and value with the maximum value
        for column in columns_to_max:
            max_row = final_merged_data[final_merged_data[column] == final_merged_data[column].max()]
            max_name = max_row["Name"].values[0]
            max_value = max_row[column].values[0]
            data_list.append([max_name, column, max_value])

        # Create a Pandas DataFrame from the list of data
        result_df = pd.DataFrame(data_list, columns=["Name", "Quality", "Value"])

        # Streamlit app
        st.title("LeaderBoard")

        # Add a button to display the LeaderBoard DataFrame
        if st.button("LeaderBoard"):
            st.dataframe(result_df)
