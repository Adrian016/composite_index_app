import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

# Load the environment variables from .env file
load_dotenv()

class DatabaseBigQuery:
    
    @staticmethod
    def connect_to_database():
        """Establish a connection to the Bigquery Datawarehouse using SQLAlchemy."""
        project = os.getenv("BQ_PROJECT")
        credentials_path = os.getenv("BQ_CREDENTIALS_PATH")
        
        datawarehouse_url = f"bigquery://{project}"
        engine = create_engine(datawarehouse_url, credentials_path=credentials_path, echo=True)
        connection = engine.connect()
        return connection
    
    @staticmethod
    def fetch_all_categories():
        """Fetch distinct values for categories from the database."""
        with DatabaseBigQuery.connect_to_database() as conn:
            query = """SELECT * 
                        FROM marts.ppi_all_commodities
                        ORDER BY category_2, category_3
                    """

            return pd.read_sql(query, conn)
    
    @staticmethod
    def fetch_series_data(category_2, category_3=None) -> list:
        """Fetch the series_id for given category_2 and optionally category_3."""
        with DatabaseBigQuery.connect_to_database() as conn:
            base_query = """
                        SELECT series_id \
                        FROM marts.ppi_series_details \
                        WHERE category_2 = %s
                        """
            params = [category_2]
            
            # If category_3 is provided, append the condition to the base query
            if category_3:
                base_query += " AND category_3 = %s"
                params.append(category_3)

            df = pd.read_sql(base_query, conn, params=tuple(params))
            return df['series_id'].tolist()
        
    @staticmethod
    def fetch_timeseries_data(series_id) -> pd.DataFrame:
        """Fetch time series data for a given series_id."""
        with DatabaseBigQuery.connect_to_database() as conn:
            query = """SELECT 
                        observation_date, 
                        adjusted_index_value 
                    FROM marts.ppi_adjusted_2020
                    WHERE series_id = %(series_id)s"""
            return pd.read_sql(query, conn, params={'series_id': series_id[0]})
