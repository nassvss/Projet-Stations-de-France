from flask import Flask, render_template, request
import pandas as pd
import requests
import time

app = Flask(__name__)

# Adresse du fichier du gouvernement (toujours à jour)
URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/csv?use_labels=true"
CARBURANTS = ["Gazole", "E10", "SP98", "SP95", "E85", "GPLc"]

# Le tableau est gardé en mémoire pour ne pas le retélécharger à chaque recherche
donnees = None
derniere_maj = 0


def charger_donnees():
    global donnees, derniere_maj
    # On retélécharge seulement si le tableau a plus de 10 minutes
    if donnees is None or time.time() - derniere_maj > 600:
        # Charger le fichier
        df = pd.read_csv(URL, sep=";")

        # Garder seulement les colonnes utiles
        df = df[["Adresse", "Ville", "Code postal", "latitude", "longitude",
                 "Prix Gazole", "Prix E10", "Prix SP98", "Prix SP95", "Prix E85", "Prix GPLc"]]

        # Mettre latitude et longitude en degrés (elles sont x 100 000 dans le fichier)
        df["latitude"] = df["latitude"] / 100000
        df["longitude"] = df["longitude"] / 100000

        donnees = df
        derniere_maj = time.time()
    return donnees.copy()


def chercher(ville, choix, rayon_km):
    df = charger_donnees()

    # Choisir la ville
    stations_ville = df[df["Ville"].str.lower() == ville.strip().lower()]
    if len(stations_ville) > 0:
        # La ville a des stations : son centre = la moyenne de leurs positions
        lat_centre = stations_ville["latitude"].mean()
        lon_centre = stations_ville["longitude"].mean()
    else:
        # Pas de station dans cette ville : on demande sa position à l'API
        reponse = requests.get("https://data.geopf.fr/geocodage/search",
                               params={"q": ville, "type": "municipality", "limit": 1})
        resultats = reponse.json()["features"]
        if len(resultats) == 0:
            return "Ville introuvable, vérifie l'orthographe !", None
        lon_centre = resultats[0]["geometry"]["coordinates"][0]
        lat_centre = resultats[0]["geometry"]["coordinates"][1]

    # Choisir le carburant
    colonne = "Prix " + choix

    # Supprimer les stations qui ne vendent pas ce carburant
    df = df.dropna(subset=[colonne])

    # Calculer la distance par rapport au centre de la ville (méthode de Pythagore)
    ecart_nord_sud = (df["latitude"] - lat_centre) * 111     # 1 degré de latitude = environ 111 km
    ecart_est_ouest = (df["longitude"] - lon_centre) * 73    # 1 degré de longitude = environ 73 km à Paris
    df["distance_km"] = (ecart_nord_sud ** 2 + ecart_est_ouest ** 2) ** 0.5

    # Garder les stations proches
    proches = df[df["distance_km"] <= rayon_km]

    if len(proches) == 0:
        return "Aucune station trouvée dans ce rayon.", None

    # Trier du moins cher au plus cher et garder les 5 premières
    proches = proches.sort_values(colonne)
    top = proches[["Adresse", "Ville", colonne, "distance_km"]].head(5)
    top = top.rename(columns={colonne: "prix"}).round({"distance_km": 1})
    return "", top.to_dict("records")


@app.route("/", methods=["GET", "POST"])
def accueil():
    message = ""
    stations = None
    if request.method == "POST":
        ville = request.form["ville"]
        choix = request.form["carburant"]
        rayon_km = float(request.form["rayon"])
        message, stations = chercher(ville, choix, rayon_km)
    return render_template("index.html", message=message, stations=stations, carburants=CARBURANTS)


if __name__ == "__main__":
    app.run(debug=True)
