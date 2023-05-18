# Ivado Labs Takehome

# Experiment

Use:
- ./data/gold.csv
- ./notebooks/notebook.py
- ./notebooks/takehome.ipynb - Colaboratory.pdf
- https://colab.research.google.com/drive/1oUlkSCSaJYBWR9vz6nvGLZ05ykHJV-VB#scrollTo=ym4EEis6ejux

## Setup

Build docker images

```
docker-compose build
```

Start database
```
docker-compose up db
```

Run tasks

```
docker-compose up ingest
docker-compose up train
docker-compose up predict
```

Shutdown

```
docker-compose down --remove-orphans
```

### Ingest

#### Bronze Table

Ingesting raw tables from https://en.wikipedia.org/wiki/List_of_most-visited_museums with minimal cleaning and stored into `bronze_museum` table with following schema:

```
{
    'name': VARCHAR(256),
    'visitors': INTEGER(),
    'city': VARCHAR(256),
    'state_or_country': VARCHAR(256),
    'state_or_country2': VARCHAR(256),
    'year': INTEGER()
}
```
#### Silver Table

Bronze table is cleaned and augmented with city metadata. For simplicity, I choosed to denormalize the city metadata instead of managing two separate tables. The cleaned and augmented data is stored in the `silver_museum` table with the following schema:

```
{
    'museum_name': VARCHAR(256),
    'city_name': VARCHAR(256),
    'country_alpha_2': VARCHAR(2),
    'city_geo_name_id': VARCHAR(32),
    'city_population': INTEGER(),
    'visitor_count': INTEGER(),
    'year': INTEGER()
}
```

### Train

To train the linear regression model, we select data from the `silve_museum` to build the `gold`  data frame with the following schema:

```
{
    'museum_name': VARCHAR(256),
    'city_population': INTEGER(),
    'visitor_count': INTEGER()
}
```

The model is computed and stored in the `models` table. We could add a version number to the model:

```
{
    'c_0': DOUBLE(),
    'c_1': DOUBLE(),
}
```


### Predict

Predict loads the model from the `models` table and computes the prediction.
