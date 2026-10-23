# Motorcyclists : when the accident happens, it is often more deadly

Dashboard Streamlit de data storytelling on the severity of physical motorcycle accidents in France between 2019 and 2024.

- **Online Application :** (URL `https://….streamlit.app`)](https://projet-moto-hipyeiaszkypfa9lxdtabk.streamlit.app)
- **Author :** Laetitia ARNOULT, EFREI Paris, groupe BIO. Individual project « Streamlit Dashboard », 2026.

## Question, audience and narrative thread

**Question.** When a bodily accident occurs, is a motorcyclist more likely to be killed than another occupant ? Does this difference varies according to age, tile, place and year ? 

**Audience.** Anyone who drives or is interested in road safety : motorcyclists, relatives, elected officials and prevention actors. Road accidents are a public health issue. The following indicator here is **lethality**, a classic public health indicator.

**Application Thread.**

1. *Hook* : un chiffre d'ouverture (rapport de létalité motard / autres occupants) et des indicateurs liés aux filtres.
2. *Contexte* : évolution année par année, avec repère sur 2020.
3. *Insights* : gravité selon l'âge, moment de la journée, carte des accidents.
4. *Implications* : synthèse, limites et pistes pour aller plus loin.

## Principal results

- **In 2024**, 5.4 % of motorcyclists involved in a personal accident were killed, compared to 2.3% of others drivers or passengers : a ratio of about 2.4
- **Sur 2019-2024** : À COMPLÉTER (reprendre les chiffres de l'encadré « Ce qu'il faut retenir » de l'application).
- À COMPLÉTER : une ligne sur ce que montre le graphique par âge, et une sur le graphique par heure.

These results describe the severity after an accident, not the risk of kilometer travelled.

## Data

| | |
|---|---|
| Source | ONISR (Observatoire national interministériel de la sécurité routière), *Bases de données annuelles des accidents corporels de la circulation routière, années de 2005 à 2024* |
| Portail | data.gouv.fr : https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024 |
| Productor | Ministry of the Interior (fichier BAAC) |
| Licence | Open Licence (Etalab) |
| Périod used | 2019 à 2024 (file structure stable since 2019) |
| Files used | by year : `caract`, `vehicules`, `usagers` (CSV). The table `lieux` is not used |
| Documentation | « Description of the annual databases of road traffic accidents resulting in personal injury, years 2005 to 2024 », ONISR, 21 october 2025 |

Basemap : © CARTO, © OpenStreetMap contributors.

Raw CSV files are not included in the repository (size). The prepared file `data/processed/usagers_2019_2024.parquet` is included so that the application functions as is.

## Method

**Unit of analysis.** The person (driver or passenger). Pedestrians are excluded : they are considered part of the vehicule that struck them.

**Definition of "motorcyclist".** Vehicule in category `catv` = 31 (motorcycle over 50cc and up to 125cc) or 33 (motorcycles over 125cc), according to the OSNIR guide. Scooters, mopeds, and motorized three-wheelers are excluded to keep the definition simple. It can be modified in one line (`MOTO_CODES` in `prepare_data.py`).

**Comparison group.** « Other occupants" : all other drivers and passengers (cars, bicycles, trucks, etc.). A filter allows comparison to be made to car occupants only (`catv` = 7).

**Indicator.** Percentage of fatalities (`grav` = 2, death at the scene or within 30 days), and ratio between the proportion among motorcyclists and other occupants. The category "hospitalized injury" is not used : it is not comparable before and after 2018 according to the OSNIR.

**Data preparation** (`prepare_data.py`).

- Reading of each year with separator detection and check of expected columns (the script stops with a clear message if a column is missing).
- Joining `usagers` ← `vehicules` on `id_vehicule`, then ← `caract` sur `Num_Acc`, with a many-to-one relationship checked (`validate="many_to_one"`) and ensuring the number of rows does not change.
- Âge = year of accident − year of birth; time extracted from `hrmn` (supported formats); latitude and longitude converted to numbers (decimal comma).
- Columns missing from certain years (for example `id_usager` in 2019) created empty, in order to be able to assemble the six years.
- Output: a single parquet file (fast to load).

**Application** (`app.py`).

- Cached data load (`st.cache_data`); pre-aggregated table based on filters applied with each interaction.

- Filters: years, months, comparison group. Indicators and graphs are based on these filters; titles and conclusions are calculated from the data.

- Map: all bikers killed are displayed; those not killed are randomly selected (seed `42`, maximum 15,000 points) to maintain a smooth map.

## Data Quality

The "Data Quality and Limitations" section of the application calculates: number of rows, duplicate user IDs, missing values ​​per variable, aberrant ages, missing equipment, missing or non-metropolitan contact details, and numbers per year.

## Limitations and Ethics

1. The database only contains individuals already involved in a traffic accident resulting in injury: it measures the severity of the accident, not the probability of having an accident. No data on kilometers traveled is available, therefore no risk per kilometer is calculated.

2. The "other occupants" group is heterogeneous.

3. Starting in 2021, hit-and-run drivers are added to the database: their sex, age, or severity of injury are often missing.

4. Not all accidents are precisely geolocated. The map reflects population and traffic density, not a risk per area.

5. Comparisons do not establish causality. The explanation based on the absence of vehicle bodywork is an untested hypothesis.

6. The user ID is absent from the 2019 database: duplicate detection only applies to the years for which entries are available.

7. 2020 is atypical (lockdowns, reduced traffic).

8. The figures include overseas territories, except for the map (metropolitan France only).

9. Some variables are intentionally omitted by the ONISR to protect privacy.

**Ethics.** Only aggregated data is presented, without individual cases or identification. The text describes situations of vulnerability and is not intended to blame motorcyclists.

## Accessibility

Dark pink on a light background for contrast, labeled axes and units, named groups on the graphs (color is not the only identifier), and a text description under each graph and map.

## Installation and Launch

Tested locally with Python 3.13.

1. Download the CSV files `caract`, `vehicules`, and `usagers` for the years 2019 to 2024 from the data.gouv.fr page mentioned above and place them in `data/raw/`, keeping the original names (the script identifies the files by a keyword in the name and by the year).

2. Create and activate a virtual environment, then install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows : .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Prepare the data (generates `data/processed/usagers_2019_2024.parquet`) :

   ```bash
   python prepare_data.py
   ```

4. Launch the application :

   ```bash
   streamlit run app.py
   ```

Step 3 can be skipped: the prepared file is provided in the repository.

## Project structure

```
.
├── app.py                       # application Streamlit
├── prepare_data.py              # Raw CSV → single parquet
├── requirements.txt             # dependencies (pinned versions)
├── README.md
├── .gitignore
├── .streamlit/config.toml       # pink theme
└── data/
    ├── raw/                     # CSV ONISR (unversioned)
    └── processed/
        └── usagers_2019_2024.parquet
```

## Reproducibility

Dependencies pinned in `requirements.txt` (Streamlit ≥ 1.33). Fixed seed (`SEED = 42`) for the map sample. Automatic checks in `prepare_data.py`: expected columns and number of rows retained after join.

## Deployment

Application deployed to Streamlit Community Cloud from this repository (main file: `app.py`).

## Suggestions for further exploration

Extend the study to 2005-2018 (different file structure), add scooters, use mileage data to measure actual risk, and compare accidents in and outside urban areas.

## Licence

Data : Open Licence (Etalab), ONISR. Code : educational project.
