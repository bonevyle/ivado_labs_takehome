import pandas as pd
import numpy as np
from sqlalchemy import create_engine
# from sqlalchemy.types import VARCHAR, INTEGER, DOUBLE


def main():
    # db_engine = create_engine('postgresql://admin:secret@localhost/database')
    db_engine = create_engine('postgresql://admin:secret@db/database')
    silver_museum_table_name = 'silver_museum'

    query = f'SELECT museum_name, city_population, visitor_count, year FROM {silver_museum_table_name}'
    gold_df = pd.read_sql(query, db_engine)

    print('-------------- TRAINING USING DATA ---------------')
    print(gold_df.to_markdown())
    print('-------------- TRAINING USING DATA ---------------')

    with open('./data/gold.csv', 'w') as file:
        file.write(gold_df.to_csv())

    # Make regression
    model = np.polyfit(gold_df['city_population'], gold_df['visitor_count'], deg=1)

    model_table_name = 'models'
    mode_df = pd.DataFrame({'c_0': [model[0]], 'c_1': [model[1]]})

    # override the whole table for simplicity... we could version the model instead
    mode_df.to_sql(model_table_name, db_engine, index=False, if_exists='replace')

    print('-------------- TRAINED MODEL ---------------')
    print(mode_df.to_markdown())
    print('-------------- TRAINED MODEL ---------------')


if __name__ == '__main__':
    main()