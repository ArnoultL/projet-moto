import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- Constantes ----------
DATA_FILE = "data/processed/usagers_2019_2024.parquet"
ANNEES = list(range(2019, 2025))
SEED = 42            # graine pour l'échantillon de points de la carte
MAX_POINTS = 15000   # nombre maximal de points sur la carte

ROSE = "#C2185B"
ROSE_CLAIR = "#F48FB1"
GRIS = "#8E7A83"

TRANCHES_BINS = [0, 18, 25, 35, 45, 55, 65, 120]
TRANCHES_LABELS = ["<18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]


# ---------- Fonctions utilitaires ----------
def style(fig):
    """Apply a consistent style to Plotly figures."""
    fig.update_layout(
        plot_bgcolor="#FFF5F8",
        paper_bgcolor="#FFF5F8",
        font=dict(color="#3A0A1F", size=14),
        showlegend=False,
    )
    return fig


def fr(x, n=1):
    """French format: decimal comma."""
    return f"{x:.{n}f}".replace(".", ",")


def nb(n):
    """French format of an integer: space as thousands separator."""
    return f"{int(n):,}".replace(",", " ")


def taux(x):
    """Percentage of people killed in a group."""
    return x["tue"].mean() * 100 if len(x) else 0


st.set_page_config(page_title="Motorcyclists: a unique risk", layout="wide")


@st.cache_data(show_spinner=False)
def load_raw():
    """Complete table prepared by prepare_data.py."""
    return pd.read_parquet(DATA_FILE)


@st.cache_data(show_spinner=False)
def load_data():
    """Drivers and passengers, with the 'groupe' column."""
    df = load_raw()
    df = df[df["catu"].isin([1, 2])].copy()  # conducteurs et passagers
    df["groupe"] = df["est_moto"].map({True: "Motard", False: "Autre occupant"})
    return df


raw = load_raw()
df = load_data()

# Title
st.title("Motorcyclists: when an accident happens, it is more often fatal")
st.caption("Source: ONISR, annual databases of personal injury accidents 2019 to 2024."
            "Data.gouv.fr, Open License.")

# Sidebar
with st.sidebar:
    if os.path.exists("assets/logo_efrei.png"):
        st.image("assets/logo_efrei.png", caption="Logo EFREI Paris")

    st.header("Filtres")
    annees = st.multiselect("Années", ANNEES, default=ANNEES)
    mois = st.slider("Mois", 1, 12, (1, 12))
    comparaison = st.selectbox(
        "Comparer les motards à",
        ["Tous les autres occupants", "Occupants de voitures seulement"],
        help="Les occupants de voitures sont les véhicules de code 7 (VL seul).",
    )

    st.divider()
    st.markdown(
        "**Laetitia Arnoult**  \n"
        "Ing2-BIO, 4th year  \n"
        "[laetitia.arnoult@efrei.net](mailto:laetitia.arnoult@efrei.net)  \n"
        "[LinkedIn](https://www.linkedin.com/in/laetitia-arnoult-862174292/) · "
        "[GitHub]https://github.com/ArnoultL/projet-moto)"
    )
    st.caption(
        "Data visualization and analysis  \n"
        "Project proposed by Prof. Mano Mathew  \n"
        "[LinkedIn](https://www.linkedin.com/in/manomathew/)"
    )

if not annees:
    st.warning("Select at least one year in the left menu.")
    st.stop()

d = df[df["annee"].isin(annees) & df["mois"].between(*mois)]
if comparaison == "Car occupants only":
    d = d[d["est_moto"] | (d["catv"] == 7)]

motards = d[d["groupe"] == "Motard"]
autres = d[d["groupe"] == "Autre occupant"]

if len(motards) == 0:
    st.warning("No bikers in this selection: broaden the filters.")
    st.stop()

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Motorcyclists involved (selected period)", nb(len(motards)))
c2.metric("Killed bikers", nb(motards["tue"].sum()))
c3.metric("% of bikers killed", f"{fr(taux(motards))} %")
c4.metric("Motorcyclist/other report",
          f"x {fr(taux(motards) / taux(autres))}" if taux(autres) else "n/a")

# ---------- Graphique 1 : comparaison ----------
if taux(autres):
    st.subheader(f"An involved biker is {fr(taux(motards) / taux(autres))} times more often killed")
else:
    st.subheader("Part de personnes tuées : motards et autres occupants")
res = d.groupby("groupe")["tue"].agg(personnes="size", tues="sum").reset_index()
res["pct_tues"] = (res["tues"] / res["personnes"] * 100).round(2)
fig1 = px.bar(
    res, x="groupe", y="pct_tues", text="pct_tues", color="groupe",
    color_discrete_map={"Motard": ROSE, "Autre occupant": GRIS},
    labels={"groupe": "Groupe", "pct_tues": "% of people killed"},
    hover_data=["personnes", "tues"],
)
st.plotly_chart(style(fig1), theme=None)
st.caption("Description: Bar chart comparing the proportion of fatalities"
            "among motorcyclists and other occupants. The figures are shown"
            "in the tooltip.")

# Graph 1
evo = (d.groupby(["annee", "groupe"])["tue"]
       .agg(personnes="size", pct="mean").reset_index())
evo["pct"] = (evo["pct"] * 100).round(2)
piv = evo.pivot(index="annee", columns="groupe", values="pct")
if {"Motard", "Autre occupant"} <= set(piv.columns) and (piv["Motard"] > piv["Autre occupant"]).all():
    st.subheader("Each year, the proportion of motorcyclists killed exceeds that of other occupants.")
else:
    st.subheader("Change in the proportion of people killed, year by year")
fig6 = px.line(
    evo, x="annee", y="pct", color="groupe", markers=True,
    color_discrete_map={"Motard": ROSE, "Autre occupant": GRIS},
    labels={"annee": "Année", "pct": "% of person killed", "groupe": "Groupe"},
    hover_data=["personnes"],
)
fig6 = style(fig6)
fig6.update_layout(showlegend=True)
fig6.update_xaxes(dtick=1)
if 2020 in annees:
    fig6.add_vline(x=2020, line_dash="dot", line_color=GRIS,
                   annotation_text="2020 : confinement", annotation_position="top")
st.plotly_chart(fig6, theme=None)
st.caption("Description: Graphs showing the proportion of people killed per year, for motorcyclists"
            "and for other occupants. The year 2020, marked by lockdowns, is"
            "indicated by a vertical line. Figures are shown in the tooltip.)")

# Graph by age
st.subheader("The proportion of motorcyclists killed tends to increase with age")
motards = motards.assign(tranche=pd.cut(motards["age"], bins=TRANCHES_BINS,
                                        labels=TRANCHES_LABELS, right=False))
age = (motards.groupby("tranche", observed=True)["tue"]
       .agg(motards="size", tues="sum").reset_index())
age["pct_tues"] = (age["tues"] / age["motards"] * 100).round(2)
fig2 = px.bar(
    age, x="tranche", y="pct_tues", color_discrete_sequence=[ROSE],
    labels={"tranche": "age", "pct_tues": "% of motorcyclists killed"},
    hover_data=["motards", "tues"],
)
st.plotly_chart(style(fig2), theme=None)
st.caption("Description: Bar chart of the proportion of motorcyclists killed by age group."
            "The figures for each age group are shown in the tooltip; the differences between neighboring age groups"
            "should be interpreted with caution.")

# Grap by hour
st.subheader("Motorcycle accidents tend to occur in the late afternoon, peaking around 5 p.m.")
heure = motards.groupby("heure").size().reset_index(name="motards")
fig3 = px.bar(
    heure, x="heure", y="motards", color_discrete_sequence=[ROSE],
    labels={"hour": "Hour of the day", "bikers": "involved bikers"},
)
st.plotly_chart(style(fig3), theme=None)
st.caption("Description: Bar chart of the number of motorcyclists involved per hour of the day."
            "The numbers are highest in the late afternoon and, to a lesser extent,"
            "in the early morning. They also reflect traffic volume: this graph does not "
            "measure risk per hour.")

# Map
st.subheader("The motorcyclists involved are concentrated around major urban areas"
                "and along the Mediterranean coast")

geo = motards.dropna(subset=["lat", "long"])
geo = geo[geo["lat"].between(41, 51.5) & geo["long"].between(-5.5, 10)]  
n_geo = len(geo)

geo_tues = geo[geo["tue"]]
geo_non_tues = geo[~geo["tue"]]
if n_geo > MAX_POINTS:
    geo_non_tues = geo_non_tues.sample(max(MAX_POINTS - len(geo_tues), 0), random_state=SEED)
geo_aff = pd.concat([geo_non_tues, geo_tues])  
geo_aff = geo_aff.assign(
    statut=geo_aff["tue"].map({True: "Tué", False: "Non tué"}),
    taille=geo_aff["tue"].map({True: 8, False: 3}),
)

fig4 = px.scatter_map(
    geo_aff, lat="lat", lon="long", color="statut", size="taille", size_max=8,
    color_discrete_map={"Tué": ROSE, "Non tué": GRIS},
    opacity=0.6, zoom=4.5, center={"lat": 46.6, "lon": 2.4}, height=600,
    map_style="carto-positron",
    hover_data={"age": True, "dep": True, "taille": False, "lat": False, "long": False},
)
fig4.update_layout(legend_title_text="Biker Status", paper_bgcolor="#FFF5F8")
st.plotly_chart(fig4, theme=None)
st.caption(
    "Description: Map of metropolitan France, one dot per motorcyclist involved"
    "(larger and darker if killed)."
    f"{nb(len(geo_aff))} points displayed on {nb(len(motards))} bikers : "
    f"{nb(len(motards) - n_geo)} do not have valid coordinates in mainland France"
    "(overseas territories included), and the motorcyclists who were not killed are shot at random"
    f"(graine {SEED}) When there are too many of them, all the motorcyclists killed are displayed."
    "The points are concentrated where the population and traffic are densest:"
    "the map does not measure risk by territory."
)

# Data quality and limitations
st.header("Data quality and limitations")

raw_motards = raw[raw["est_moto"] & raw["catu"].isin([1, 2])]

q1, q2, q3 = st.columns(3)
q1.metric("Lines (users, 2019-2024)", nb(len(raw)))
ids = raw["id_usager"].dropna()
q2.metric("Duplicate user IDs (years entered)", nb(ids.duplicated().sum()))
q3.metric("Age missing (bikers)", f"{fr(raw_motards['age'].isna().mean() * 100)} %")

st.markdown("**Bikers involved and killed, year by year**")
par_an = (raw_motards.groupby("annee")["tue"]
          .agg(motards="size", tues="sum").reset_index())
par_an["% tués"] = (par_an["tues"] / par_an["motards"] * 100).round(2)
par_an["annee"] = par_an["annee"].astype(str)
st.dataframe(par_an, hide_index=True)

st.markdown("**Missing values ​​per variable (bikers)**")
manq = (raw_motards.isna().mean() * 100).round(1).sort_values(ascending=False)
manq = manq[manq > 0].rename("% manquant").to_frame()
st.dataframe(manq)

st.markdown("**Validity checks**")
age_ok = raw_motards["age"].dropna()
lat_ok = pd.to_numeric(raw_motards["lat"], errors="coerce")
lon_ok = pd.to_numeric(raw_motards["long"], errors="coerce")
sans_geo = int((~(lat_ok.between(41, 51.5) & lon_ok.between(-5.5, 10))).sum())
checks = pd.DataFrame({
    "Control": [
        "Negative age or over 100 years",
        "Equipment not specified (secu1 = -1)",
        "No equipment declared (secu1 = 0)",
        "GPS coordinates missing or outside mainland France (including overseas territories)",
    ],
    "Lines concerned": [
        int(((age_ok < 0) | (age_ok > 100)).sum()),
        int((raw_motards["secu1"] == -1).sum()),
        int((raw_motards["secu1"] == 0).sum()),
        sans_geo,
    ],
})
st.dataframe(checks, hide_index=True)

st.warning(
    "**Boundaries.** \n\n" 
    "(1) The file only contains people already involved in a personal injury accident: we measure the severity, not the probability of having an accident, and no data on kilometers travelled is available. \n\n "
    "(2) The group 'other occupants' mixes cars, bicycles, heavy goods vehicles, etc. \n\n"
    "(3) From 2021 onwards, users who have fled are added to the database: their sex, age, or severity of their condition are often missing. \n\n"
    "(4) Not all accidents are precisely geolocated. \n\n"
    "(5) A comparison does not establish causality. \n\n"
    "(6) The user ID is absent from the 2019 files: duplicate detection therefore only applies to the years for which information is provided. \n\n"
    "(7) The year 2020 is atypical (lockdowns, reduced movement): to be interpreted with caution. \n\n"
    "(8) Figures include overseas territories, except for the map (metropolitan France only). \n\n"
    "(9) The severity of 'hospitalized injury' is not comparable before and after 2018: "
    "only the proportion of people killed is used here."
)

# st.subheader("Un accident de moto est-il plus souvent mortel hors agglomération ?")
# motards = motards.assign(
#    zone=motards["agg"].map({1: "Hors agglomération", 2: "En agglomération"})
# )
# zone = (motards.dropna(subset=["zone"]).groupby("zone")["tue"]
#         .agg(motards="size", tues="sum").reset_index())
# zone["pct_tues"] = (zone["tues"] / zone["motards"] * 100).round(2)
# fig5 = px.bar(
#     zone, x="zone", y="pct_tues", color_discrete_sequence=[ROSE],
#     labels={"zone": "Localisation", "pct_tues": "% de motards tués"},
#     hover_data=["motards", "tues"],
# )
# st.plotly_chart(style(fig5), theme=None)

#Conclusion
st.header("Key takeaways")
m = df[df["groupe"] == "Motard"]
a = df[df["groupe"] == "Autre occupant"]
periode = f"{int(df['annee'].min())} à {int(df['annee'].max())}"

m_age = m.assign(tranche=pd.cut(m["age"], bins=TRANCHES_BINS,
                                labels=TRANCHES_LABELS, right=False))
t_age = m_age.groupby("tranche", observed=True)["tue"].agg(n="size", pct="mean")
p35 = t_age.loc["35-44", "pct"] * 100
p65 = t_age.loc["65+", "pct"] * 100
n65 = int(t_age.loc["65+", "n"])

if p65 > p35:
    phrase_age = (
        f"The proportion of fatalities tends to increase with age: it goes from approximately {fr(p35)} % "
        f"among 35-44 year olds {fr(p65)} % among those aged 65 and over ({nb(n65)} bikers), "
        "which suggests paying particular attention to older motorcyclists. "
        "Differences between neighboring groups should be interpreted with caution. "
    )
else:
    phrase_age = (
        "The proportion of fatalities varies according to age, with no clear trend between the 35-44 age group."
        f"({fr(p35)} %) and those aged 65 and over ({fr(p65)} %). "
    )

st.success(
    f"**Key insight.** Over the period {periode}, {fr(taux(m))} % bikers involved in "
    f"a traffic accident resulted in fatalities, against {fr(taux(a))} % of others "
    f"occupants (x {fr(taux(m) / taux(a))}).\n\n"
    f"**Implications.** Once the accident has occurred, a motorcyclist is approximately"
    f"{fr(taux(m) / taux(a))} times more often killed than any other occupant, which can"
    "can be explained by the absence of a bodywork rather than by behavior "
    "(hypothesis not tested here). "
    f"{phrase_age}"
    "These results describe the severity of accidents, not the risk per kilometer traveled, and do not allow us to isolate a cause.\n\n"
    "**Suggestions for further exploration:** Extend the data to 2005-2018 (different file structure), add scooters, use distance traveled " \
    "data to measure true risk, and compare accidents in and outside urban areas."
)
