import pandas as pd

import pandas as pd


def df_cleaning(df):
    # Select relevant columns
    df = df[['Datum', 'Naam / Omschrijving', 'Af Bij', 'Bedrag (EUR)', 'Saldo na mutatie']]

    # Rename 'Naam / Omschrijving' to 'Naam'
    df.rename(columns={'Naam / Omschrijving': 'Naam'}, inplace=True)

    # Replace commas with dots and convert to float
    df['Bedrag (EUR)'] = df['Bedrag (EUR)'].str.replace(',', '.').astype(float)
    df['Saldo na mutatie'] = df['Saldo na mutatie'].str.replace(',', '.').astype(float)

    # Negate values where 'Af Bij' is 'Af'
    df.loc[df['Af Bij'] == 'Af', 'Bedrag (EUR)'] = -abs(df['Bedrag (EUR)'])

    # Drop the 'Af Bij' column
    df.drop('Af Bij', axis=1, inplace=True)

    # Convert 'Datum' to datetime format
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y%m%d')

    return df


# Example usage:
input_df = pd.read_csv('bank_transactions.csv', sep=';')
processed_df = df_cleaning(input_df)



