import requests #68S617QRYKZHX4ZN #I1TVUXGTKDYPXB78
import pandas as pd
import streamlit as st 
import plotly 
import numpy as np
import psycopg2, psycopg2.extras
import plotly.graph_objects as go
import altair as alt
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
from features.functions import *
import os 


#____________________________________________Import_données_+_nettoyage __________________________________________________________

df_coffee = pd.read_csv("df_coffee.csv", index_col=None)
df_coffee = clean_df(df_coffee,'coffee')

df_coffee_mm = df_coffee.copy()
df_coffee_les = df_coffee.copy()
df_coffee_led = df_coffee.copy()
df_coffee_hw = df_coffee.copy()
#_______________________________________________Parametres__________________________________________________

st.header('Prévision pour les prochains mois')
forecast_horizon = st.sidebar.number_input(
    'Entrez le nombre de mois à prévoir:', 
    min_value=1,  # Valeur minimale de 1 mois
    max_value=24,  # Valeur maximale de 12 mois
    value=12,  # Valeur par défaut
    step=1  # Incrément de 1 pour chaque pas
)

st.header('Choix des paramètres')
alpha = st.sidebar.number_input(
    'Choisissez la valeur alpha :', 
    min_value=0.0,  # Valeur minimale de 1 mois
    max_value=1.0,  # Valeur maximale de 12 mois
    value=0.1,  # Valeur par défaut
    step=0.1  # Incrément de 1 pour chaque pas
)

beta = st.sidebar.number_input(
    'Choisissez la valeur beta :', 
    min_value=0.0,  # Valeur minimale de 1 mois
    max_value=1.0,  # Valeur maximale de 12 mois
    value=0.1,  # Valeur par défaut
    step=0.1  # Incrément de 1 pour chaque pas
)

gamma = st.sidebar.number_input(
    'Choisissez la valeur gamma :', 
    min_value=0.0,  # Valeur minimale de 1 mois
    max_value=1.0,  # Valeur maximale de 12 mois
    value=0.1,  # Valeur par défaut
    step=0.1  # Incrément de 1 pour chaque pas
)

season_length = st.sidebar.number_input(
    'Choisissez la saisonnalité :', 
    min_value=1,  # Valeur minimale de 1 mois
    max_value=12,  # Valeur maximale de 12 mois
    value=12,  # Valeur par défaut
    step=1 # Incrément de 1 pour chaque pas
)

#_______________________________________________________________________________________________________________________

current_month_start = pd.to_datetime('today').replace(day=1)  # Remplace le jour par 1 pour obtenir le début du mois actuel

df_coffee_mm.index = pd.date_range(start=current_month_start , periods=len(df_coffee_mm), freq='-1MS')  # Index mensuel descendant

# Étape 2 : Calcul des prévisions avec un index d'extension
last_date = df_coffee_mm.index[0]  # Première date historique
forecast_index = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_horizon, freq='MS')

# Prévisions de MM (Simples moyennes mobiles)
df_mm = pd.DataFrame(
    moyenne_mobile_simple(df_coffee_mm['value_coffee'], 4, forecast_horizon),
    index=forecast_index,  # Index des prévisions
    columns=['MM']
)

# Étape 3 : Construire les deux parties
# Partie historique : valeurs historiques, MM=NaN
df_historical = df_coffee_mm.copy()
df_historical['MM'] = np.nan

# Partie prévisions : value_coffee=NaN, valeurs MM
df_forecast = pd.DataFrame(index=forecast_index)
df_forecast['value_coffee'] = np.nan
df_forecast['MM'] = df_mm['MM']

df_forecast = df_forecast[::-1]

# Étape 4 : Concaténation des données historiques et des prévisions
df_final = pd.concat([df_forecast, df_historical])

# Étape 5 : Affichage dans Streamlit
st.subheader('Prévision selon la méthode des moyennes mobiles')
st.dataframe(df_final)
st.line_chart(df_final)
#_______________________________________________________________________________________________________________________
# Étape 1 : Préparer les données

df_coffee_les.index = pd.date_range(start=current_month_start , periods=len(df_coffee_les), freq='-1MS')  # Index mensuel descendant

# Étape 2 : Calcul des prévisions avec un index d'extension
last_date = df_coffee_les.index[0]  # Première date historique (la plus récente)
forecast_index = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_horizon, freq='MS')

# Lissage exponentiel simple (modifié pour ordre décroissant)
_, forecasts = lissage_exponentiel_simple(df_coffee_les['value_coffee'].values, alpha, forecast_horizon)

# Étape 3 : Construire les deux parties du dataframe final
# Partie historique : uniquement les données brutes historiques
df_historical = df_coffee_les.copy()

# Partie prévisions : uniquement les prévisions SES
df_forecast = pd.DataFrame(index=forecast_index[::-1])  # Inverser l'ordre de l'index
df_forecast['value_coffee'] = np.nan  # Aucune donnée brute pour les prévisions
df_forecast['LES'] = forecasts        # Ajouter les prévisions SES

# Étape 4 : Concaténation
df_final = pd.concat([df_forecast, df_historical])

# Étape 5 : Affichage

st.subheader('Prévisions selon la méthode du Lissage Exponentiel Simple (LES)')
st.line_chart(df_final[['value_coffee', 'LES']])

#_______________________________________________________________________________________________________________________
df_coffee_led.index = pd.date_range(start=current_month_start , periods=len(df_coffee_led), freq='-1MS')  # Index mensuel descendant

# Étape 2 : Calcul des prévisions LED avec un index d'extension
last_date = df_coffee_led.index[0]  # Première date historique (la plus récente)
forecast_index = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_horizon, freq='MS')

# Lissage exponentiel double (LED)
_, forecasts = lissage_exponentiel_double(df_coffee_led['value_coffee'].values, alpha, beta, forecast_horizon)

# Inverser les prévisions pour qu'elles aillent du futur au plus récent
forecasts = forecasts[::-1]

# Étape 3 : Construire les deux parties du dataframe final
# Partie historique : uniquement les données brutes historiques
df_historical = df_coffee_led.copy()

# Partie prévisions : uniquement les prévisions LED
df_forecast = pd.DataFrame(index=forecast_index[::-1])  # Inverser l'ordre de l'index
df_forecast['value_coffee'] = np.nan  # Aucune donnée brute pour les prévisions
df_forecast['LED'] = forecasts        # Ajouter les prévisions LED

# Étape 4 : Concaténation
df_final = pd.concat([df_forecast, df_historical])

# Étape 5 : Affichage

st.subheader('Prévisions selon la méthode du Lissage Exponentiel Simple (LED)')
st.line_chart(df_final[['value_coffee', 'LED']])

#_______________________________________________________________________________________________________________________


# Étape 1 : Configuration de l'index mensuel descendant pour les données historiques
df_coffee_hw.index = pd.date_range(start='2024-09', periods=len(df_coffee_hw), freq='-1MS')  # Index mensuel descendant

# Étape 2 : Calcul des prévisions Holt-Winters avec un index d'extension
last_date = df_coffee_hw.index[0]  # Première date historique (la plus récente)
forecast_index = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_horizon, freq='MS')


# Validation de la longueur des données par rapport à la saisonnalité
if len(df_coffee_hw) < season_length:
    st.error("Les données historiques doivent contenir au moins autant d'observations que la saisonnalité.")
else:
    # Prévisions avec Holt-Winters
    _, forecasts = holt_winters(df_coffee_hw['value_coffee'].values, alpha, beta, gamma, season_length, forecast_horizon)

    # Inverser les prévisions pour qu'elles aillent du futur au présent
    forecasts = forecasts[::-1]

    # Étape 3 : Construire les deux parties du dataframe final
    # Partie historique : uniquement les données brutes historiques
    df_historical = df_coffee_hw.copy()

    # Partie prévisions : uniquement les prévisions HW
    df_forecast = pd.DataFrame(index=forecast_index[::-1])  # Inverser l'ordre de l'index
    df_forecast['value_coffee'] = np.nan  # Aucune donnée brute pour les prévisions
    df_forecast['HW'] = forecasts         # Ajouter les prévisions Holt-Winters

    # Étape 4 : Concaténation
    df_final = pd.concat([df_forecast, df_historical])

    # Étape 5 : Affichage
st.subheader('Prévisions selon la méthode de Holt & Winter')
st.line_chart(df_final[['value_coffee', 'HW']])