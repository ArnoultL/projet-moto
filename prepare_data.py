"""Prepare user's table 2019-2024 from ONSIR's csv"""
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
YEARS = range(2019, 2025)
MOTO_CODES = [31, 33]   
MOTS_CLES = {"caract": "carac", "lieux": "lieux", "vehicules": "vehic", "usagers": "usag"}


def find_file(kind, year):
    trouves = [p for p in RAW.glob("*.csv")
               if MOTS_CLES[kind] in p.name.lower() and str(year) in p.name]
    if len(trouves) != 1:
        raise FileNotFoundError(f"{kind} {year} : {len(trouves)} file(s) found in {RAW}")
    return trouves[0]


def read(path):
    with open(path, encoding="utf-8-sig", errors="ignore") as f:
        sep = ";" if ";" in f.readline() else ","
    df = pd.read_csv(path, sep=sep, encoding="utf-8-sig", low_memory=False)
    df.columns = df.columns.str.strip()
    return df.rename(columns={"Accident_Id": "Num_Acc"})


def need(df, cols, nom, year):
    manquantes = [c for c in cols if c not in df.columns]
    if manquantes:
        raise KeyError(f"{nom} {year} : colonnes absentes {manquantes}. Colonnes : {list(df.columns)}")


def to_float(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "."), errors="coerce")


def heure(s):
    s = s.astype(str)
    h = s.str.split(":").str[0].where(s.str.contains(":"), s.str.zfill(4).str[:2])
    return pd.to_numeric(h, errors="coerce")


def prepare_year(year):
    caract = read(find_file("caract", year))
    vehicules = read(find_file("vehicules", year))
    usagers = read(find_file("usagers", year))

    need(caract, ["Num_Acc", "jour", "mois", "hrmn", "dep", "lat", "long"], "caract", year)
    need(vehicules, ["Num_Acc", "id_vehicule", "catv"], "vehicules", year)
    need(usagers, ["Num_Acc", "id_vehicule", "catu", "grav", "an_nais"], "usagers", year)

    vehicules["est_moto"] = vehicules["catv"].isin(MOTO_CODES)
    df = usagers.merge(vehicules[["id_vehicule", "catv", "est_moto"]],
                       on="id_vehicule", how="left", validate="many_to_one")
    assert len(df) == len(usagers), f"{year} : la jointure a modifié le nombre de lignes"

    cols_c = [c for c in ["Num_Acc", "jour", "mois", "hrmn", "dep", "agg", "lat", "long"] if c in caract.columns]
    df = df.merge(caract[cols_c], on="Num_Acc", how="left", validate="many_to_one")

    df["annee"] = year
    for c in ["id_usager", "secu1", "agg"]:
        if c not in df.columns:
            df[c] = pd.NA
    df["est_moto"] = df["est_moto"].fillna(False).astype(bool)
    df["tue"] = df["grav"] == 2
    df["age"] = year - pd.to_numeric(df["an_nais"], errors="coerce")
    df["heure"] = heure(df["hrmn"])
    df["lat"], df["long"] = to_float(df["lat"]), to_float(df["long"])

    m = df[df["est_moto"] & df["catu"].isin([1, 2])]
    print(f"{year} : {len(df):>7} users | {len(m):>6} motorcyclists | {int(m['tue'].sum()):>4} killed | "
          f"lat [{m['lat'].min():.1f} ; {m['lat'].max():.1f}] | missing age {m['age'].isna().mean()*100:.1f} %")
    return df[["annee", "Num_Acc", "id_usager", "catv", "est_moto", "catu", "grav", "tue",
               "sexe", "age", "secu1", "mois", "heure", "dep", "agg", "lat", "long"]]


def main():
    tables = [prepare_year(y) for y in YEARS]
    out = pd.concat(tables, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT / "usagers_2019_2024.parquet", index=False)
    print(f"\n{len(out)} lines written")


if __name__ == "__main__":
    main()
