import requests
import os
import zipfile
from tqdm import tqdm  # Importer la bibliothèque tqdm pour la barre de progression

download_dir = "unsplash_dataset"


def download_unsplash_dataset(download_dir):
    url = "https://unsplash.com/data/lite/latest"

    # Télécharger le fichier ZIP avec une barre de progression verte
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise ValueError(
            f"Impossible de télécharger le fichier. Code d'état HTTP : {response.status_code}")

    # Enregistrer le fichier ZIP avec une barre de progression verte
    zip_file_path = os.path.join(download_dir, "unsplash_dataset.zip")
    with open(zip_file_path, "wb") as f:
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB',
                            unit_scale=True, desc="Téléchargement", colour='green')
        for chunk in response.iter_content(chunk_size=block_size):
            progress_bar.update(len(chunk))
            if chunk:
                f.write(chunk)
    progress_bar.close()

    # Décompresser le fichier ZIP
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)
    except zipfile.BadZipFile:
        raise ValueError("Le fichier ZIP est corrompu ou invalide")

    # Supprimer le fichier ZIP s'il a été décompressé avec succès
    os.remove(zip_file_path)
