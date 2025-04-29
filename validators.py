import os
import logging
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()


class ExcelValidator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = pd.read_excel(file_path)

    def check_consistency(self):

        grouped_df = self.df.groupby('companynameofficial')['geonameen'].nunique()
        inconsistent_geonames = grouped_df[grouped_df > 1].index

        # Mark inconsistent companies and geonames
        self.df['companynameofficial_inconsistent'] = self.df['companynameofficial'].isin(inconsistent_geonames)
        self.df['geonameen_inconsistent'] = self.df['geonameen'].isin(inconsistent_geonames)

        return self.df

    def check_accuracy(self, threshold=3):
        grouped_revenue = self.df.groupby(['companynameofficial', 'geonameen'])['REVENUE'].sum().reset_index()

        # Detect outliers based on the z score method
        mean = np.mean(grouped_revenue['REVENUE'])
        std_dev = np.std(grouped_revenue['REVENUE'])

        if std_dev == 0:
            return []
        
        z_scores = (grouped_revenue['REVENUE'] - mean) / std_dev
        grouped_revenue['is_outlier'] = np.abs(z_scores) > threshold

        # Merge back the outlier info into the original dataframe
        self.df = self.df.merge(
            grouped_revenue[['companynameofficial', 'geonameen', 'is_outlier']],
            on=['companynameofficial', 'geonameen'],
            how='left'
        )

        self.df['revenue_outlier_flag'] = self.df['is_outlier'].fillna(False)
        self.df.drop(columns=['is_outlier'], inplace=True)

        return self.df
    
    def check_outlier(self):
        features = self.df[['REVENUE']].dropna()

        # Standardize the features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        dbscan = DBSCAN(eps=0.5, min_samples=5)
        dbscan.fit(features_scaled)

        # Don't add cluster labels to the DataFrame
        self.df['dbscan_cluster'] = None
        self.df.loc[features.index, 'dbscan_cluster'] = dbscan.labels_

        # Identify outliers (label -1)
        self.df['dbscan_outlier_flag'] = self.df['dbscan_cluster'] == -1

        return self.df
    
    def check_iqr_range(self):
        company_revenue_stats = self.df.groupby("companynameofficial")["REVENUE"].mean().reset_index()
        company_revenue_stats.rename(columns={"REVENUE": "mean_revenue"}, inplace=True)

        # Calculate IQR to flag outliers
        Q1 = company_revenue_stats["mean_revenue"].quantile(0.25)
        Q3 = company_revenue_stats["mean_revenue"].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q1 + 1.5 * IQR

        # Identify outliers
        outliers = company_revenue_stats[
            (company_revenue_stats["mean_revenue"] < lower_bound) |
            (company_revenue_stats["mean_revenue"] > upper_bound)
        ]

        self.df["IQR_outlier_flag"] = False
        self.df.loc[outliers.index, "IQR_outlier_flag"] = True

        return self.df
    
    
    def check_correctness(self):
        self.df['negative_revenue_flag'] = self.df['REVENUE'] <= 0
        self.df[self.df['negative_revenue_flag']]

        return self.df
    
    
    def validate_all(self):
        self.check_consistency()
        self.check_accuracy()
        self.check_correctness()
        self.check_outlier()
        self.check_iqr_range()

        return self.df
    

class CurrencyCheckerLLM:
    def __init__(self, model_name="gpt-3.5-turbo", batch_size=5, max_retries=3, retry_delay=5):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Ensure that the API key is set
        if self.api_key is None:
            raise ValueError("OpenAI API key not found in environment variables")

        # Initialize the OpenAI client with the API key
        self.client = OpenAI(api_key=self.api_key)

        self.model_name = model_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _build_prompt(self, rows):
        prompt_intro = (
            "Return True if the currency is NOT the official one for the country; else False.\n"
            "Format: CUR | COUNTRY → True/False\n"
            "Examples:\n"
            "EUR | United Kingdom → True\n"
            "GBP | United Kingdom → False\n"
            "USD | USA → False\n"
            "CAD | France → True\n"
            "Now check:\n"
        )
        formatted_rows = [f"{row['unit_REVENUE']} | {row['geonameen']}" for _, row in rows.iterrows()]
        prompt = prompt_intro + "\n" + "\n".join(formatted_rows)
        return prompt

    def _query_llm(self, rows):
        prompt = self._build_prompt(rows)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            lines = response.choices[0].message.content.strip().splitlines()
            return [line.strip() for line in lines if "True" in line or "False" in line]
        except Exception as e:
            logging.error(f"Error processing batch: {e}")
            return ["False"] * len(rows)

    def _apply_flags(self, df, start_idx, responses):
        df.loc[start_idx:start_idx + len(responses) - 1, "currency_check_flag"] = [
            "true" in r.lower() for r in responses
        ]

    def check_currency(self, df):
        df = df.copy()
        df["currency_check_flag"] = False

        for start in range(0, len(df), self.batch_size):
            end = min(start + self.batch_size, len(df))
            batch = df.iloc[start:end]
            responses = self._query_llm(batch)
            self._apply_flags(df, start, responses)
            logging.info(f"Processed rows {start}–{end - 1}")

        return df