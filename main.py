import csv
import os
import urllib.request
import zipfile
from urllib.error import HTTPError


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


def download_images(data, nb_images):
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "bigdata/bigdata_app/data/images")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Vérifier si le dossier "images" est vide
    if os.path.exists(dir_path) and os.listdir(dir_path):
        print("Le dossier 'images' n'est pas vide. Pas de téléchargement nécessaire.")
    else:
        for i in range(nb_images):
            # Chemin complet vers le fichier image
            filepath = os.path.join(dir_path, data[i][0] + ".jpg")
            image_url = data[i][2]

            try:
                # Télécharger l'image et l'enregistrer dans le dossier "images"
                urllib.request.urlretrieve(image_url, filepath)
                print("Image " + image_url + " OK " + str(i+1) + "/" + str(nb_images))
            except HTTPError as e:
                if e.code == 404:
                    print("Image " + image_url + " ERR 404 " + str(i+1) + "/" + str(nb_images))
                else:
                    print("Image " + image_url + " ERR " + str(i+1) + "/" + str(nb_images), e)

if __name__ == "__main__":
    url = "https://unsplash.com/data/lite/latest"
    folder_name = "unsplash-research-dataset-lite-latest"
    file_name = "photos.tsv000"
    nb_images = 500

    download_and_extract_data(url, folder_name, file_name)
    download_images(csv.reader(open(os.path.join(folder_name, file_name), "r"), delimiter="\t"), nb_images)
