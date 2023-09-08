import streamlit as st
import pandas as pd
import io
from io import BytesIO
import plotly.express as px
import plotly.graph_objs as go
import base64  # Format conversion ke liye


# Page Configuration Setup kar rhe
st.set_page_config(page_title="END OF SEASON")

# Sidebar DropDown
st.sidebar.title("Select Number of Clans")
num_clans = st.sidebar.selectbox("Number of Clans", [2, 3, 4, 5, 6, 7, 8])

# Upload Files Section
st.sidebar.title("Upload Files")
file_uploads = {}
for i in range(1, num_clans + 1):
    st.sidebar.subheader(f"Clan {i}")
    for j in range(1, 3):
        unique_key = f"clan_{i}_file_{j}"
        label = "Season" if j == 1 else "War"  # Label the first file upload as "Season" and the second as "War"
        file_upload = st.sidebar.file_uploader(f"Upload {label} File for Clan {i}", type=["xlsx"], key=unique_key)
        if file_upload:
            key_name = f"Clan {i}, {label}"
            file_uploads[key_name] = file_upload

# Type Menu Dropdown ke liye
sort_order = st.selectbox("Type", ["War Stars", "Top Member", "Donations", "EOS Trophies","Capital Gold Contributed","Capital Gold Looted","Main Base","Builder Base","Capital","All"])
with st.spinner("Loading..."):
    # Place the code that updates the display inside the spinner context
    for key, value in file_uploads.items():
        # st.subheader(key)
        if value:
            file_data = value.read()  # Read the file data
            file_name = value.name
            file_size = value.size
            # st.write(f"File Name: {file_name}")
for key, value in file_uploads.items():
    # st.subheader(key)
    if value:
        file_data = value.read()  # Read the file data
        file_name = value.name
        file_size = value.size
        # st.write(f"File Name: {file_name}")

# Saari Clans ki files check krne ke baad show karna hai
if len(file_uploads) == num_clans * 2:  # Assuming 2 files for each clan
    # Function to preprocess the data
    def preprocess_data(wars_file, season_file):
        wars = pd.read_excel(wars_file)
        season = pd.read_excel(season_file)
        clan = wars.merge(season, on="Name", how="outer")

        clan.drop(columns={'Def Stars', 'Avg. Def Stars',
       'Total Def Dest', 'Avg. Def Dest', 'Tag_y','War-Stars Gained',
       'CWL-Stars Gained', 'Gold Looted', 'Elixir Lotted', 'Dark Elixir Looted',
       'Clan Games','Tag_x','Discord',"Town Hall_x","Town Hall_y"},inplace=True)
        clan.rename(columns={"Total Attacks_y":"Total War Attacks", 'Total Attacks_x':"Attacks in a Season",'Month_y':"Month"},inplace=True)
        clan['Total War Attacks'].fillna(clan['Total War Attacks'].min(),inplace=True)
        clan['Total Stars'].fillna(clan['Total Stars'].min(),inplace=True)
        clan['True Stars'].fillna(clan['True Stars'].min(),inplace=True)
        clan['Avg. True Stars'].fillna(clan['Avg. True Stars'].min(),inplace=True)
        clan['Avg. Stars'].fillna(clan['Avg. Stars'].min(),inplace=True)
        clan['Total Dest'].fillna(clan['Total Dest'].min(),inplace=True)
        clan['Avg. Dest'].fillna(clan['Avg. Dest'].min(), inplace=True)
        clan['Two Stars'].fillna(clan['Two Stars'].min(),inplace=True)
        clan['One Stars'].fillna(clan['One Stars'].min(),inplace=True)
        clan['Zero Stars'].fillna(clan['Zero Stars'].min(),inplace=True)
        clan['Three Stars'].fillna(clan['Three Stars'].min(),inplace=True)
        clan['Missed'].fillna(clan['Missed'].min(),inplace=True)
        clan['Total Donated'].fillna(0,inplace=True)
        clan['Total Received'].fillna(0,inplace=True)
        clan['Attacks in a Season'].fillna(0,inplace=True)
        clan['Versus Attacks'].fillna(0,inplace=True)
        clan['Trophies Gained'].fillna(0,inplace=True)
        clan['Season-End Trophies'].fillna(clan['Season-End Trophies'].min(),inplace=True)
        clan['Versus-Trophies Gained'].fillna(0,inplace=True)
        clan['Capital Gold Looted'].fillna(0,inplace=True)
        clan['Capital Gold Contributed'].fillna(0,inplace=True)
        clan['Activity Score'].fillna(clan['Activity Score'].min(),inplace=True)
        def war_score_func(value):
            ul=clan['Total Stars'].quantile(0.75)
            ll=clan['Total Stars'].quantile(0.25)
            war_score=0.6*(value-ll)*10.0/(ul-ll)
            return war_score
        clan["War Score"]=clan["Total Stars"].apply(war_score_func)
        def donation_score_func(value):
            ul=clan['Total Donated'].quantile(0.75)
            ll=clan['Total Donated'].quantile(0.25)
            donation_score=0.3*(value-ll)*10.0/(ul-ll)
            return donation_score
        clan["Donation Score"]=clan["Total Donated"].apply(donation_score_func)
        def activity_score_func(value):
            ul=clan['Activity Score'].quantile(0.75)
            ll=clan['Activity Score'].quantile(0.25)
            final_activty_score=0.1*(value-ll)*10.0/(ul-ll)
            return final_activty_score
        clan["Final Activty Score"]=clan["Activity Score"].apply(activity_score_func)
        def missed_attack_function(value):
            missed_attack_score=(value)**2
            return missed_attack_score
        clan["Missed Attack Score"]=clan["Missed"].apply(missed_attack_function)
        clan= clan.assign(season_score=clan['War Score'] + clan['Donation Score']+clan['Final Activty Score']-clan['Missed Attack Score'])

        return clan

    # Empty list to store preprocessed dataframes for each clan
    all_clan_data = []

    # Iterate through each Clan and preprocess the data
    for i in range(1, num_clans + 1):
        season_key = f"Clan {i}, Season"
        war_key = f"Clan {i}, War"

        if season_key in file_uploads and war_key in file_uploads:
            season_file = file_uploads[season_key]
            war_file = file_uploads[war_key]

            if season_file is not None and war_file is not None:
                clan_data = preprocess_data(season_file, war_file)
                all_clan_data.append(clan_data)

    if all_clan_data:
        final_merged_data = pd.concat(all_clan_data, ignore_index=True)

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
        final_merged_data.drop(columns={"Final Activty Score","Activity Score","Missed Attack Score"},inplace=True)
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
                fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
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
                fig.update_traces(texttemplate='%{text:.4s}',textposition='outside')

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
            fig=px.bar(display_df,x=display_df.Name,y='season_score',color="season_score",text='season_score',hover_data=["Total Stars","Total Donated","season_score","Season-end Trophies"],hover_name="Name",title='Best Performers',height=500,width=700,color_continuous_scale='YlOrRd')
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

