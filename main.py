import pandas as pd
import requests

# Charger le fichier
url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-instantane-v2/exports/csv?use_labels=true"
df = pd.read_csv(url, sep=";")

# Garder seulement les colonnes utiles
df = df[["Adresse", "Ville", "Code postal", "latitude", "longitude",
         "Prix Gazole", "Prix E10", "Prix SP98", "Prix SP95", "Prix E85", "Prix GPLc"]]

# Mettre latitude et longitude en degrés (elles sont x 100 000 dans le fichier)
df["latitude"] = df["latitude"] / 100000
df["longitude"] = df["longitude"] / 100000

# Choisir la ville
while True:
    ville = input("Entrez une ville ? : ")
    stations_ville = df[df["Ville"].str.lower() == ville.strip().lower()]
    if len(stations_ville) > 0:
        # La ville a des stations : son centre = la moyenne de leurs positions
        lat_centre = stations_ville["latitude"].mean()
        lon_centre = stations_ville["longitude"].mean()
        break
    else:
        # Pas de station dans cette ville : on demande sa position à l'API
        print("Pas de station dans cette ville, je cherche sa position...")
        reponse = requests.get("https://data.geopf.fr/geocodage/search",
                               params={"q": ville, "type": "municipality", "limit": 1})
        resultats = reponse.json()["features"]
        if len(resultats) > 0:
            print("Ville trouvée :", resultats[0]["properties"]["label"])
            lon_centre = resultats[0]["geometry"]["coordinates"][0]
            lat_centre = resultats[0]["geometry"]["coordinates"][1]
            break
        else:
            print("Ville introuvable, vérifie l'orthographe !")

# Choisir le carburant
while True:
    choix = input("Quel carburant (Gazole, E10, SP98, SP95, E85, GPLc) ? : ")
    colonne = "Prix " + choix
    if colonne in df.columns:
        break  # Le carburant existe donc on break pour passer a la suite
    else:
        print("Carburant inconnu, réessaye avec un nom valide !")

# Supprimer les stations qui ne vendent pas ce carburant
df = df.dropna(subset=[colonne])

# Calculer la distance par rapport au centre de la ville (méthode de Pythagore)
ecart_nord_sud = (df["latitude"] - lat_centre) * 111     # 1 degré de latitude = environ 111 km
ecart_est_ouest = (df["longitude"] - lon_centre) * 73    # 1 degré de longitude = environ 73 km à Paris
df["distance_km"] = (ecart_nord_sud ** 2 + ecart_est_ouest ** 2) ** 0.5

# Garder les stations proches
rayon_km = float(input("Entrez un rayon? : "))

proches = df[df["distance_km"] <= rayon_km]

# Trier du moins cher au plus cher et afficher les 5 premières
if len(proches) == 0:
    print("Aucune station trouvée dans ce rayon.")
else:
    proches = proches.sort_values(colonne)
    print(proches[["Adresse", "Ville", colonne, "distance_km"]].head(5).to_string())