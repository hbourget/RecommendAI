import os
import csv
import urllib.request
import zipfile
from urllib.error import HTTPError

# URL de l'archive ZIP de Unsplash Lite
url = "https://unsplash.com/data/lite/latest"
folder_name = "unsplash-research-dataset-lite-latest"
file_name = "photos.tsv000"

if not os.path.exists(folder_name) or not os.path.isfile(os.path.join(folder_name, file_name)):
    # Téléchargement de l'archive ZIP et ouverture en mode lecture binaire
    with urllib.request.urlopen(url) as response:
        content = response.read()

    # Écriture de l'archive ZIP dans un fichier temporaire
    with open("unsplash-research-dataset-lite-latest.zip", "wb") as f:
        f.write(content)

    # Extraction de l'archive ZIP
    with zipfile.ZipFile("unsplash-research-dataset-lite-latest.zip", "r") as zip_ref:
        zip_ref.extractall("unsplash-research-dataset-lite-latest")

# Parcours des fichiers TSV extraits et lecture de leurs données
data = []
for file in os.listdir("unsplash-research-dataset-lite-latest"):
    if file.endswith("photos.tsv000"):
        with open(os.path.join("unsplash-research-dataset-lite-latest", file), "r", encoding="utf8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                data.append(row)

dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
if not os.path.exists(dir_path):
    os.makedirs(dir_path)

# Vérifier si le dossier "images" est vide
if os.path.exists(dir_path) and os.listdir(dir_path):
    print("Le dossier 'images' n'est pas vide. Pas de téléchargement nécessaire.")
else:
    nbImages = 500
    for i in range(1,500):
        # Chemin complet vers le fichier image
        filepath = os.path.join(dir_path, data[i][0] + ".jpg")

        try:
            # Télécharger l'image et l'enregistrer dans le dossier "images"
            urllib.request.urlretrieve(data[i][2], filepath)
            print("Image "+ data[i][2] +" OK " + i.__str__() + "/500")
        except HTTPError as e:
            if e.code == 404:
                print("Image "+ data[i][2] +" ERR 404 " + i.__str__() + "/500")
            else:
                print("Image "+ data[i][2] +" ERR " + i.__str__() + "/500", e)

