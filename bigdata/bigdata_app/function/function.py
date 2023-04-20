import csv
import urllib.request
import zipfile
import os
import json
import numpy as np
import exifread
from keras.applications import EfficientNetB0
from keras.utils import load_img, img_to_array
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

input_file = '../data/unsplash-research-dataset-lite-latest/photos.tsv000'
output_dir = '../data/images/'
url = 'https://unsplash.com/data/lite/latest'
zip_file = '../data/unsplash-research-dataset-lite-latest.zip'
extract_dir = '../data/unsplash-research-dataset-lite-latest'


def download_unsplash_dataset(url, zip_file, extract_dir):
    # Check if the extract directory already exists
    if os.path.isdir(extract_dir):
        print(f'Unsplash dataset is already extracted in {extract_dir}')
        return

    # Check if the zip file exists and is not empty
    if not os.path.exists(zip_file):
        print('Downloading Unsplash dataset...')
        urllib.request.urlretrieve(url, zip_file)
    elif os.path.getsize(zip_file) == 0:
        os.remove(zip_file)
        print(f'Removing empty zip file {zip_file}')
        print('Downloading Unsplash dataset...')
        urllib.request.urlretrieve(url, zip_file)
    else:
        print(f'Zip file {zip_file} already exists and is not empty.')

    # Extract the zip file
    if os.path.exists(zip_file):
        with zipfile.ZipFile(zip_file) as zf:
            zf.extractall(extract_dir)

        print(f'Unsplash dataset extracted to {extract_dir}')
    else:
        print(f'Zip file {zip_file} does not exist.')


def download_images(input_file, output_dir, num_images):
    # Check if the output directory exists
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    # Check if the input file exists
    if not os.path.exists(input_file):
        print(f'Input file {input_file} does not exist.')
        return

    # Check if the input file is not empty
    if os.path.getsize(input_file) == 0:
        print(f'Input file {input_file} is empty.')
        return

    # Check if the specified number of images has already been downloaded
    downloaded_images = [f for f in os.listdir(output_dir) if
                         f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    if len(downloaded_images) >= num_images:
        print(f"The output directory {output_dir} already contains at least {num_images} images.")
        return

    # Download the images
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for i, row in enumerate(reader):
            if i >= num_images:
                break

            try:
                image_url = row['photo_image_url']
                image_path = os.path.join(output_dir, f"{row['photo_id']}.jpg")

                # Check if the image has already been downloaded
                if os.path.exists(image_path):
                    continue

                urllib.request.urlretrieve(image_url, image_path)

                print(f"Downloaded image {i + 1}/{num_images}: {image_path}")
            except Exception as e:
                print(f"Failed to download image {i + 1}: {str(e)}")

    # Count the number of downloaded images
    downloaded_images = [f for f in os.listdir(output_dir) if
                         f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    num_downloaded_images = len(downloaded_images)
    print(f"Downloaded a total of {num_downloaded_images} images.")

    # Check if any images were downloaded
    if num_downloaded_images == 0:
        print('No images were downloaded.')


# Cache for the model
model_cache = None

# Load and cache the model
def load_model():
    global model_cache
    if model_cache is None:
        model_cache = EfficientNetB0(weights='imagenet')
    return model_cache

# Classify an image
def classify_image(image_path):
    # Load and preprocess the image
    img = load_img(image_path, target_size=(224, 224))
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    # Use the model to classify the image
    model = load_model()
    preds = model.predict(x)
    decoded_preds = decode_predictions(preds, top=10)[0]

    # Return a list of tags
    tags = [pred[1] for pred in decoded_preds]
    return tags


def extract_image_metadata(input_dir, output_file):
    # Check if the input directory exists
    if not os.path.isdir(input_dir):
        print(f'Input directory {input_dir} does not exist.')
        return

    # Check if the output file exists
    if os.path.exists(output_file):
        print(f'Output file {output_file} already exists.')
        return

    # Extract metadata from images
    metadata = []
    for file in os.listdir(input_dir):
        if file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.png'):
            file_path = os.path.join(input_dir, file)
            try:
                with open(file_path, 'rb') as f:
                    tags = classify_image(file_path)
                    exif_tags = exifread.process_file(f, details=False, stop_tag='UNDEF')
                    metadata.append({
                        'filename': file,
                        'tags': {str(tag): str(value) for tag, value in exif_tags.items() if tag != 'JPEGThumbnail'},
                        'image_tags': tags
                    })
            except Exception as e:
                print(f"Failed to extract metadata from {file}: {str(e)}")

    # Write metadata to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)

    print(f"Metadata extracted from {len(metadata)} images and saved to {output_file}")



def add_user_preference(user_id, image_id, preferences_file='../data/user_preferences.json'):
    if not os.path.exists(preferences_file):
        with open(preferences_file, 'w') as f:
            json.dump([], f)

    with open(preferences_file, 'r') as f:
        preferences = json.load(f)

    preference = {'user_id': user_id, 'image_id': image_id}
    preferences.append(preference)

    with open(preferences_file, 'w') as f:
        json.dump(preferences, f)


def content_based_recommendation(user_id, metadata_file='../data/metadata.json', preferences_file='../data/user_preferences.json'):
    # Charger les métadonnées des images et les préférences des utilisateurs
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    with open(preferences_file, 'r') as f:
        preferences = json.load(f)

    # Filtrer les images aimées par l'utilisateur
    user_preferences = [p for p in preferences if p['user_id'] == user_id]
    liked_images = [p['image_id'] for p in user_preferences]

    # Créer un dictionnaire pour associer les ID d'image aux tags
    image_tags = {item['filename']: ' '.join(item['image_tags']) for item in metadata}

    # Utiliser un TfidfVectorizer pour transformer les tags en vecteurs
    vectorizer = TfidfVectorizer()
    image_vectors = vectorizer.fit_transform(image_tags.values())

    # Calculer les similarités entre les images
    similarity_matrix = cosine_similarity(image_vectors)

    # Trouver les indices des images aimées par l'utilisateur
    liked_image_indices = [list(image_tags.keys()).index(img_id) for img_id in liked_images]

    # Calculer les scores de recommandation pour chaque image en fonction de leur similarité
    recommendation_scores = np.sum(similarity_matrix[liked_image_indices], axis=0)

    # Trouver les indices des images recommandées
    recommended_image_indices = np.argsort(recommendation_scores)[::-1]

    # Retourner les ID des images recommandées
    recommended_image_ids = [list(image_tags.keys())[index] for index in recommended_image_indices]

    # Filtrer les images déjà aimées par l'utilisateur
    recommended_image_ids = [img_id for img_id in recommended_image_ids if img_id not in liked_images]

    return recommended_image_ids[:10]



def collaborative_filtering_recommendation(user_id, preferences_file='../data/user_preferences.json', k=10):
    # Charger les préférences des utilisateurs
    with open(preferences_file, 'r') as f:
        preferences = json.load(f)
    # Créer une matrice utilisateur-image
    user_ids = sorted(list(set([p['user_id'] for p in preferences])))
    image_ids = sorted(list(set([p['image_id'] for p in preferences])))

    user_id_to_index = {user_id: index for index, user_id in enumerate(user_ids)}
    image_id_to_index = {image_id: index for index, image_id in enumerate(image_ids)}

    user_image_matrix = np.zeros((len(user_ids), len(image_ids)))

    for preference in preferences:
        user_index = user_id_to_index[preference['user_id']]
        image_index = image_id_to_index[preference['image_id']]
        user_image_matrix[user_index, image_index] = 1

    # Utiliser NearestNeighbors pour trouver les utilisateurs similaires
    model_knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=k, n_jobs=-1)
    model_knn.fit(csr_matrix(user_image_matrix))

    user_index = user_id_to_index[user_id]

    # Trouver les k voisins les plus proches
    k = min(k, user_image_matrix.shape[0] - 1)  # Ajoutez cette ligne pour limiter k
    distances, indices = model_knn.kneighbors(user_image_matrix[user_index].reshape(1, -1), n_neighbors=k + 1)

    # Trouver les images préférées par les utilisateurs similaires
    similar_users_indices = indices.flatten()[1:]
    similar_users_preferences = defaultdict(int)

    for index in similar_users_indices:
        for i, value in enumerate(user_image_matrix[index]):
            if value == 1:
                image_id = image_ids[i]
                similar_users_preferences[image_id] += 1

    # Trier les images en fonction de leur popularité parmi les utilisateurs similaires
    recommended_image_ids = sorted(similar_users_preferences, key=similar_users_preferences.get, reverse=True)

    # Filtrer les images déjà aimées par l'utilisateur
    user_liked_images = [p['image_id'] for p in preferences if p['user_id'] == user_id]
    recommended_image_ids = [img_id for img_id in recommended_image_ids if img_id not in user_liked_images]

    return recommended_image_ids[:10]



def hybrid_recommendation(user_id, alpha=0.5, metadata_file='../data/metadata.json', preferences_file='../data/user_preferences.json', k=10):
    content_based_recs = content_based_recommendation(user_id, metadata_file, preferences_file)
    collaborative_recs = collaborative_filtering_recommendation(user_id, preferences_file, k)

    # Combiner les scores de recommandation des deux approches
    combined_scores = defaultdict(float)
    for i, image_id in enumerate(content_based_recs):
        combined_scores[image_id] += (1 - alpha) * (len(content_based_recs) - i)

    for i, image_id in enumerate(collaborative_recs):
        combined_scores[image_id] += alpha * (len(collaborative_recs) - i)

    # Trier les images en fonction de leur score de recommandation combiné
    recommended_image_ids = sorted(combined_scores, key=combined_scores.get, reverse=True)

    return recommended_image_ids[:10]




if __name__ == '__main__':
    # Download the Unsplash dataset
    download_unsplash_dataset(url, zip_file, extract_dir)

    # Download the images
    num_images = 500
    download_images(input_file, output_dir, num_images)

    # Extract metadata from the images
    input_dir = '../data/images/'
    output_file = '../data/metadata.json'
    extract_image_metadata(input_dir, output_file)

    # Simuler les préférences des utilisateurs
    add_user_preference(1, 'liZpmbRG4WQ.jpg')
    add_user_preference(1, 'FJc8DIDMGek.jpg')
    add_user_preference(2, '4_Bc9CSm70A.jpg')
    add_user_preference(2, '9CjgeMAM2SI.jpg')
    add_user_preference(3, '731BXpcasJI.jpg')
    add_user_preference(3, 'AMuKRdPBuek.jpg')

    # Tester les recommandations basées sur le contenu
    content_recs = content_based_recommendation(1)
    print("Recommandations basées sur le contenu pour l'utilisateur 1:")
    print(content_recs)

    # Tester les recommandations par filtrage collaboratif
    collaborative_recs = collaborative_filtering_recommendation(1)
    print("Recommandations par filtrage collaboratif pour l'utilisateur 1:")
    print(collaborative_recs)

    # Tester les recommandations hybrides
    hybrid_recs = hybrid_recommendation(1)
    print("Recommandations hybrides pour l'utilisateur 1:")
    print(hybrid_recs)