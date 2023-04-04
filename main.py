import csv
import json
import os
import urllib.request
import zipfile

def download_and_extract_data(url, folder_name, file_name):
    # Vérifier si le dossier existe et si le fichier est présent
    if not os.path.exists(folder_name) or not os.path.isfile(os.path.join(folder_name, file_name)):
        # Téléchargement de l'archive ZIP et ouverture en mode lecture binaire
        print("Téléchargement de l'archive ZIP à l'adresse " + url)
        with urllib.request.urlopen(url) as response:
            content = response.read()

        # Écriture de l'archive ZIP dans un fichier temporaire
        with open("unsplash-research-dataset-lite-latest.zip", "wb") as f:
            f.write(content)

        print("Extraction de l'archive ZIP")
        # Extraction de l'archive ZIP
        with zipfile.ZipFile("unsplash-research-dataset-lite-latest.zip", "r") as zip_ref:
            zip_ref.extractall(folder_name)

def read_data_and_save_as_json(folder_name, file_name):
    print("Parcours des fichiers TSV et lecture des données")
    # Parcours des fichiers TSV extraits et lecture de leurs données
    data = []
    for file in os.listdir(folder_name):
        if file.endswith(file_name):
            with open(os.path.join(folder_name, file), "r", encoding="utf8") as f:
                reader = csv.reader(f, delimiter="\t")
                for row in reader:
                    data.append(row)
                    # créer une entrée JSON pour chaque ligne
                    entry = {'colonne1': row[0], 'colonne2': row[1], 'colonne3': row[2]}
                    with open('data.json', 'a', encoding='utf8') as json_file:
                        json.dump(entry, json_file, ensure_ascii=False)
                        json_file.write('\n') # ajouter une nouvelle ligne pour chaque entrée JSON

def download_images(data, nb_images):
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Vérifier si le dossier "images" est vide
    if os.path.exists(dir_path) and os.listdir(dir_path):
        print("Le dossier 'images' n'est pas vide. Pas de téléchargement nécessaire.")
    else:
        for i in range(0, nb_images):
            # Chemin complet vers le fichier image
            filepath = os.path.join(dir_path, data[i][0] + ".jpg")

            try:
                # Télécharger l'image et l'enregistrer dans le dossier "images"
                urllib.request.urlretrieve(data[i][2], filepath)
                print("Image "+ data[i][2] +" OK " + str(i+1) + "/" + str(nb_images))
            except HTTPError as e:
                if e.code == 404:
                    print("Image "+ data[i][2] +" ERR 404 " + str(i+1) + "/" + str(nb_images))
                else:
                    print("Image "+ data[i][2] +" ERR " + str(i+1) + "/" + str(nb_images), e)

def main():
    url = "https://unsplash.com/data/lite/latest"
    folder_name = "unsplash-research-dataset-lite-latest"
    file_name = "photos.tsv000"
    nb_images = 500

    download_and_extract_data(url, folder_name, file_name)
    read_data_and_save_as_json(folder_name, file_name)

    # Charger les données à partir du fichier JSON
    with open('data.json', 'r', encoding='utf8') as json_file:
        data = json.load(json_file)

    download_images(data, nb_images)