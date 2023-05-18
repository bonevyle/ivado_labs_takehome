import pandas as pd
from sqlalchemy import create_engine


def predict_visitor_count(model, city_population):
    count =  model[0] * city_population + model[1]
    print(f'predicted visitors for population {city_population}: {count}')

def main():
    # db_engine = create_engine('postgresql://admin:secret@localhost/database')
    db_engine = create_engine('postgresql://admin:secret@db/database')
   
    # load first model
    model_table_name = 'models'
    query = f'SELECT c_0, c_1 FROM {model_table_name} LIMIT 1'
    model_df = pd.read_sql(query, db_engine)

    model = model_df.iloc[0].to_list()
    
    predict_visitor_count(model, 100)
    predict_visitor_count(model, 1000)
    predict_visitor_count(model, 10000)
    predict_visitor_count(model, 100000)
    predict_visitor_count(model, 1000000)

    # ingest_from_api()

if __name__ == '__main__':
    main()