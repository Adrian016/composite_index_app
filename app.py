import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db import DatabaseBigQuery as db


class PlotManager:
    """
    PlotManager Class: This static class is used to handle the generation of plots, keeping all plotting logic separate from the core Streamlit application logic. 
    """
    
    @staticmethod
    def generate_plot(aggregated_index, individual_indexes, index_categories):
        """
        The generate_plot method is designed to be generic enough to be reusable in different scenarios where such a plot is needed.
        """
        
        # Filter and plot
        last_date = aggregated_index['observation_date'].max()
        start_date = last_date - pd.DateOffset(years=5)
        filtered_data = aggregated_index[aggregated_index['observation_date'] >= start_date]

        # Create a line plot using graph_objects for more flexibility
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=filtered_data['observation_date'], 
                                 y=filtered_data['adjusted_index_value'], 
                                 mode='lines', 
                                 name='Composite Index',
                                 line={'color':'#093D44', 'width':5}))

        for idx_data, label in zip(individual_indexes, index_categories):
            idx_data = idx_data[idx_data['observation_date'] >= start_date]
            fig.add_trace(go.Scatter(x=idx_data['observation_date'], 
                                     y=idx_data['adjusted_index_value'], 
                                     mode='lines', 
                                     name=label,
                                     line=dict(color='#71869d' ,width=1),),
                         )

        fig.update_layout(title="Composite Index and Individual Indices - Last 5 Years",
                          autosize=True,)
        return fig


class StreamlitApp:
    def __init__(self):
        self.df_categories = db.fetch_all_categories()
    
        st.set_page_config(page_title="Product Composite Index", page_icon="favicon.ico", layout="wide")
        

    def gather_user_inputs(self):
        """
        gather_user_inputs Method: Encapsulates the logic to capture user inputs from Streamlit's UI.
        """
        selections = []
        
        col_num_categories, col_weights = st.columns([0.5, .5])
        
        # Get the number of categories dynamically using a slider 
        num_categories = col_num_categories.slider("Select number of categories:", min_value=1, max_value=10, value=3)
        
        if 'selections' not in st.session_state:
            st.session_state.selections = [(None, None, 0.0) for _ in range(num_categories)]
      
        # Adjust the length of st.session_state.selections to match num_categories
        while len(st.session_state.selections) < num_categories:
            st.session_state.selections.append((None, None, 0.0))
    
        while len(st.session_state.selections) > num_categories:
            st.session_state.selections.pop()
        
        with st.expander("Select Categories and Weights", expanded=True):
            for i in range(num_categories):
                col1, col2, col3 = st.columns([0.3, .5, .2])
                category_2_options = self.df_categories['category_2'].unique().tolist()
                selected_category_2 = col1.selectbox(label=f'Select Category 2 - {i+1}', options=category_2_options,
                                                     index=category_2_options.index(st.session_state.selections[i][0]) 
                                                     if st.session_state.selections[i][0] in category_2_options else 0)
                filtered_df_3 = self.df_categories[self.df_categories['category_2'] == selected_category_2]
                category_3_options = filtered_df_3['category_3'].unique().tolist()
                selected_category_3 = col2.selectbox(label=f'Select Category 3 - {i+1}', options=category_3_options,
                                                     index=category_3_options.index(st.session_state.selections[i][1]) 
                                                     if st.session_state.selections[i][1] in category_3_options else 0
                                                        )
                weight = col3.number_input(label=f"Weight % - {i+1}", min_value=0.0, max_value=100.0, step=10.0,help=None,
                                           value=st.session_state.selections[i][2]
                                           )
                selections.append((selected_category_2, selected_category_3, weight))
                
                # Update the session state with the new selections
        st.session_state.selections = selections
        return selections

    def process_data(self, selections):
        """
        process_data Method: Processes the user input to fetch the necessary data and prepare it for plotting.
        """
        individual_indexes = []  # List to store individual timeseries
        index_categories = []  # List to store index categories
        index_ids = []  # List to store index names
        weighted_dataframes = []  # List to store weighted timeseries data for merging

        for idx, selection in enumerate(selections, 1):
            series_id = db.fetch_series_data(selection[0], selection[1])
            
            if series_id:
                timeseries_data = db.fetch_timeseries_data(series_id)
                timeseries_data['observation_date'] = pd.to_datetime(timeseries_data['observation_date'])

                # Make a deep copy of the unweighted data to store in the individual_indexes list
                individual_indexes.append(timeseries_data.sort_values(by='observation_date').copy())
                
                # Store index details
                index_ids.append(f"{series_id[0]}")
                index_categories.append(f"{selection[1]}")

                # Multiply the index value by the weight and store in the weighted list
                timeseries_data['adjusted_index_value'] = timeseries_data['adjusted_index_value'] * (selection[2]/100)
                weighted_dataframes.append(timeseries_data)

        # Aggregate weighted data
        if weighted_dataframes:
            aggregated_index = pd.concat(weighted_dataframes).groupby('observation_date').sum().reset_index()
            aggregated_index = aggregated_index.sort_values(by='observation_date')
        else:
            aggregated_index = pd.DataFrame()

        return aggregated_index, individual_indexes, index_categories, index_ids
  
    def run(self):
        """
        run Method: This method serves as the entry point to execute the Streamlit application. It manages the flow by calling other methods in a sequence that makes sense. This method initializes the page, gathers user input, processes the data, generates a plot, and then displays data in Streamlit.
        """
            
        #st.title(':green[PDT Composite Product Index]')
        hide_decoration_bar_style = '''
                                        <style>
                                            header {visibility: hidden;}
                                        </style>
                                    '''
        st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: left; color: #093D44;'>PDT Composite Product Index</h1>", unsafe_allow_html=True)

        st.markdown("""So, what's the Composite Product Index? Imagine getting a bunch of product prices from different industries and mixing them all together into one super index. Now, not all products weigh the same, right? Some might be a bigger deal in a product's recipe (or bill of materials, in fancy terms), and that's where our index gets interesting. It gives more weight to those super important ingredients.""")
        st.markdown("""Why should businesses care? Well, this index is like a weather vane, pointing out the breezes and storms in the world of commodities. By keeping an eye on it, companies get a heads-up on any cool or not-so-cool changes in the market. It's like a cheat sheet for them to plan their next moves, whether it's to dodge a curveball or grab an opportunity.""")

        st.subheader('Step 1: Input BOM Commodity Cost Drivers Details')
        st.markdown(""" 
                    The interface below is designed to help you select the specific commodity categories and weights that are relevant for YOUR specific product composite index. Please select the most representative commodities based on your product BOM.
                    """)
        st.info("Please note: This app might go to sleep after a few minutes of inactivity. If you find it unresponsive, simply refresh the page.")




        selections = self.gather_user_inputs()
        st.markdown("Note: Make sure the weights add up to 100%")
        if st.button('Submit'):
            with st.spinner('Processing... This might take a moment while we fetch the requested data.'):

                aggregated_index, individual_indexes, index_categories, index_ids = self.process_data(selections)
                
                st.subheader('Step 2: View Composite Index and Individual Indices')
                
                fig = PlotManager.generate_plot(aggregated_index, individual_indexes, index_categories)
                st.plotly_chart(fig, use_container_width=True)

                # Display the aggregated index dataframe in Streamlit
                # Iterate over each dataframe and set 'observation_date' as the index
                for df in individual_indexes:
                    df.set_index('observation_date', inplace=True)

                # Rename the 'adjusted_index_value' column to the series_id and store these dataframes in a new list
                renamed_dfs = []
                for df, name in zip(individual_indexes, index_categories):
                    # Check if dataframe with same column name already exists in renamed_dfs
                    if not any(name in df_sub.columns for df_sub in renamed_dfs):
                        renamed_dfs.append(df.rename(columns={'adjusted_index_value': name}))

                #Join all the dataframes on 'observation_date'
                master_df = pd.concat(renamed_dfs, axis=1)

            

                # Display the master dataframe in Streamlit
                st.text("Master Data Frame for Chosen Categories")
                st.dataframe(master_df.reset_index())
        
        # Display logo in footer
        _, logo_placeholder, _ = st.columns([7, 2 , 7])  # Adjusting the size ratio of the columns as needed
        logo_placeholder.image("logo.png")


if __name__ == "__main__":
    app = StreamlitApp()
    app.run()
