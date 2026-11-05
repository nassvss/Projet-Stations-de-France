import pandas as pd

# Charger le fichier
df = pd.read_csv("prix-des-carburants-en-france-flux-instantane-v2.csv", sep=";")

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
        break  # La ville existe donc on passe à la suite
    else:
        print("Ville introuvable, réessaye (vérifie l'orthographe) !")

# Le centre de la ville = la moyenne des positions de ses stations
lat_centre = stations_ville["latitude"].mean()
lon_centre = stations_ville["longitude"].mean()

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