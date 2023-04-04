import requests
import os
import zipfile


def download_unsplash_dataset(url, download_dir):
    """
    Télécharge et décompresse le dataset d'image Unsplash.
    Args:
        url (str): L'URL du fichier ZIP à télécharger.
        download_dir (str): Le chemin du répertoire où le fichier doit être enregistré.
    Returns:
        None
    """
    # Télécharger le fichier ZIP
    response = requests.get(url)

    # Vérifier si la réponse a un code d'état valide
    if response.status_code != 200:
        raise ValueError(f"Impossible de télécharger le fichier. Code d'état HTTP : {response.status_code}")

    # Enregistrer le fichier ZIP
    zip_file_path = os.path.join(download_dir, "unsplash_dataset.zip")
    with open(zip_file_path, "wb") as f:
        f.write(response.content)

    # Décompresser le fichier ZIP
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(download_dir)
    except zipfile.BadZipFile:
        raise ValueError("Le fichier ZIP est corrompu ou invalide")

    # Supprimer le fichier ZIP s'il a été décompressé avec succès
    os.remove(zip_file_path)

if __name__ == "__main__":
    url = "https://unsplash.com/data/lite/latest"
    download_dir = "unsplash_dataset"
    download_unsplash_dataset(url, download_dir)
