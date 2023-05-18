import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.types import VARCHAR, INTEGER
import geonamescache
import pycountry

def ingest_from_wikipedia():
    wikiContent = requests.get('https://en.wikipedia.org/wiki/List_of_most_visited_museums').text

    parsedContent = BeautifulSoup(wikiContent, 'html.parser')
    # print(parsedContent.prettify())
    # tables = parsedContent.find_all('table', {'class': 'wikitable sortable'})
    tables = parsedContent.find_all('table', attrs={'class': 'wikitable sortable'})

    df = clean_wiki_table(tables[0], year=2022)
    df = pd.concat([df, clean_wiki_table(tables[1], year=2021)], ignore_index=True)
    df = pd.concat([df, clean_wiki_table(tables[2], year=2020)], ignore_index=True)
    df = pd.concat([df, clean_wiki_table(tables[3], year=2019)], ignore_index=True)

    print(df.to_markdown)

    return df

def clean_wiki_table(table, year):
    df = pd.read_html(str(table))[0]
    visitor_column_name=df.columns[2]
    df = df.rename(columns={'Name': 'name', 'Location': 'location', visitor_column_name: 'visitors'})

    # We want to split into: city, state_or_country, country, but sometimes only 2 are provided.
    # So, add missing columns and fill with None
    desired_column_count = 3
    splitted = df['location'].str.split(',', n=desired_column_count-1, expand=True)
    # print(splitted.to_markdown())

    # Fill
    actual_column_count = splitted.shape[1] 
    if actual_column_count < desired_column_count:
        num_additional_columns = desired_column_count - actual_column_count
        additional_columns = pd.DataFrame(data=np.full((len(df), num_additional_columns), None), columns=range(actual_column_count, desired_column_count))
        splitted = pd.concat([splitted, additional_columns], axis=1)

    splitted.columns = ['city', 'state_or_country', 'state_or_country2']
    df = pd.concat([df, splitted], axis=1)

    df = df.drop('location', axis=1)
    df['visitors'] = df['visitors'].str.extract(r'([0-9,]+)')
    df['visitors'] = df['visitors'].str.replace(',', '')
    df['name'] = df['name'].str.replace('^\. ', '', regex=True)
    df['name'] = df['name'].str.strip()
    df['city'] = df['city'].str.strip()
    df['state_or_country'] = df['state_or_country'].str.strip()
    df['state_or_country2'] = df['state_or_country2'].str.strip()

    df['year'] = year

    # print(df.to_markdown)
    return df



def silver_from_bronze_museum(bronze_df):
    # Proper city name
    gc = geonamescache.GeonamesCache()
    schema = {
        'museum_name': str,
        'city_name': str,
        'country_alpha_2': str,
        'city_geo_name_id': int,
        'city_population': int,
        'visitor_count': int,
        'year': int
    }

    silver_df = pd.DataFrame(columns=schema.keys()).astype(schema)

    for index, row in bronze_df.iterrows():
        museum_name = row['name']
        city = row['city']
        state_or_country = row['state_or_country']
        state_or_country2 = row['state_or_country2']
        year = row['year']

        country_alpha_2 = None
        found_countries = None
        if state_or_country != None:
            try:
                found_countries = pycountry.countries.search_fuzzy(state_or_country)
            except:
                pass
        if (found_countries == None and state_or_country2 != None):
            try:
                found_countries = pycountry.countries.search_fuzzy(state_or_country2)
            except:
                pass
        
        if (found_countries != None):
            country_alpha_2 = found_countries[0].alpha_2


        # Fix city name
        city_name = None
        city_geo_name_id = None
        city_population = None
        visitor_count = row['visitors']
        cities = gc.search_cities(city, case_sensitive=False)
        if (len(cities) == 1):
            city_name = cities[0]['name']
            city_geo_name_id = cities[0]['geonameid']
            city_population = cities[0]['population']
            country_alpha_2 = c['countrycode']
        else:
            for c in cities:
                if c['countrycode'] == country_alpha_2:
                    city_name = c['name']
                    city_geo_name_id = c['geonameid']
                    city_population = c['population']
                # print(c)

        if city_name == None:
            # try alternate name (like Washington DC)
            cities = gc.search_cities(f'{city} {state_or_country}', case_sensitive=False)
            if (len(cities) == 1):
                city_name = cities[0]['name']
                city_geo_name_id = cities[0]['geonameid']
                city_population = cities[0]['population']
                country_alpha_2 = c['countrycode']


        if city_name != None:
            # Only Append clean data to our silver table
            silver_row = {'museum_name': museum_name, 'city_name': city_name, 'country_alpha_2': country_alpha_2, 'city_geo_name_id': city_geo_name_id, 'city_population': city_population, 'visitor_count': visitor_count, 'year': year}
            silver_df = pd.concat([silver_df, pd.DataFrame([silver_row])], ignore_index=True)
    
    return silver_df


def main():
    bronze_df = ingest_from_wikipedia()

    print('-------------- RAW DATA BRONZE TABLE ---------------')
    print(bronze_df.to_markdown())
    print('-------------- RAW DATA BRONZE TABLE ---------------')

    with open('./data/bronze.md', 'w') as file:
        file.write(bronze_df.to_markdown())

    # db_engine = create_engine('postgresql://admin:secret@localhost/database')
    db_engine = create_engine('postgresql://admin:secret@db/database')
    bronze_museum_table_name = 'bronze_museum'

    column_data_types = {'name': VARCHAR(256), 'visitors': INTEGER(), 'city': VARCHAR(256), 'state_or_country': VARCHAR(256), 'state_or_country2': VARCHAR(256), 'year': INTEGER()}
    bronze_df.to_sql(bronze_museum_table_name, db_engine, index=False, if_exists='replace', dtype=column_data_types)

    # query = f'SELECT * FROM {bronze_museum_table_name}'
    # df = pd.read_sql(query, db_engine)

    # print(df.to_markdown())

    silver_df = silver_from_bronze_museum(bronze_df)
    with open('./data/silver.md', 'w') as file:
        file.write(silver_df.to_markdown())

    with open('./data/silver.csv', 'w') as file:
        file.write(silver_df.to_csv())

    silver_museum_table_name = 'silver_museum'
    silver_column_data_types = {'museum_name': VARCHAR(256), 'city_name': VARCHAR(256), 'country_alpha_2': VARCHAR(2), 'city_geo_name_id': VARCHAR(32), 'city_population': INTEGER(), 'visitor_count': INTEGER(), 'year': INTEGER()}
    silver_df.to_sql(silver_museum_table_name, db_engine, index=False, if_exists='replace', dtype=silver_column_data_types)

    print('-------------- CLEANED DATA SILVER TABLE ---------------')
    print(silver_df.to_markdown())
    print('-------------- CLEANED DATA SILVER TABLE ---------------')


if __name__ == '__main__':
    main()