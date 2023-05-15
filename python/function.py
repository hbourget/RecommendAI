import csv
import os
import urllib.request
import zipfile
from collections import defaultdict

import exifread
import numpy as np
import tqdm
from keras.applications import EfficientNetB0
from keras.applications.resnet import preprocess_input, decode_predictions
from keras.utils import load_img, img_to_array
from pymongo import MongoClient
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

input_file = '/data/unsplash-research-dataset-lite-latest/photos.tsv000'
output_dir = '/data/images/'
url = 'https://unsplash.com/data/lite/latest'
zip_file = '/data/unsplash-research-dataset-lite-latest.zip'
extract_dir = '/data/unsplash-research-dataset-lite-latest'


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
        # Determine the file's size before downloading
        file_size = int(urllib.request.urlopen(url).info().get('Content-Length', -1))
        print(file_size)
        # Set up the progress bar
        with tqdm(unit='B', unit_scale=True, unit_divisor=1024, total=file_size) as pbar:
            urllib.request.urlretrieve(url, zip_file, reporthook=lambda blocks, block_size, total_size: pbar.update(
                block_size * blocks))

        print(f'Unsplash dataset downloaded to {zip_file}')
    else:
        print(f'Zip file {zip_file} already exists and is not empty.')

    # Extract the zip file
    if os.path.exists(zip_file):
        print("Extracting Unsplash dataset...")
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

        for i, row in tqdm.tqdm(enumerate(reader), total=num_images):
            if i >= num_images:
                break

            try:
                image_url = row['photo_image_url']
                image_path = os.path.join(output_dir, f"{row['photo_id']}.jpg")

                # Check if the image has already been downloaded
                if not os.path.exists(image_path):
                    urllib.request.urlretrieve(image_url, image_path)
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


def extract_image_metadata(input_dir, db_collection):
    # Check if the input directory exists
    if not os.path.isdir(input_dir):
        print(f'Input directory {input_dir} does not exist.')
        return

    # Connect to the MongoDB client
    client = MongoClient("mongodb://mongo:27017/")
    db = client["image_db"]
    collection = db[db_collection]

    # Extract metadata from images
    metadata = []
    for file in os.listdir(input_dir):
        if file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.png'):
            file_path = os.path.join(input_dir, file)
            try:
                with open(file_path, 'rb') as f:
                    tags = classify_image(file_path)
                    exif_tags = exifread.process_file(f, details=False, stop_tag='UNDEF')
                    doc = {
                        'filename': file,
                        'tags': {str(tag): str(value) for tag, value in exif_tags.items() if tag != 'JPEGThumbnail'},
                        'image_tags': tags
                    }
                    collection.insert_one(doc)  # insert the document into MongoDB
                    metadata.append(doc)
            except Exception as e:
                print(f"Failed to extract metadata from {file}: {str(e)}")

    print(f"Metadata extracted from {len(metadata)} images and inserted into MongoDB")


def add_user_preference(user_id, image_id, db_collection):
    # Connect to the MongoDB client
    client = MongoClient("mongodb://mongo:27017/")
    db = client["image_db"]
    collection = db[db_collection]

    preference = {'user_id': user_id, 'image_id': image_id}
    collection.insert_one(preference)  # insert the document into MongoDB


def content_based_recommendation(user_id, db_collection_metadata, db_collection_preferences):
    # Connect to the MongoDB client
    client = MongoClient("mongodb://mongo:27017/")
    db = client["image_db"]

    # Load image metadata and user preferences from MongoDB
    metadata_collection = db[db_collection_metadata]
    preferences_collection = db[db_collection_preferences]
    metadata = list(metadata_collection.find())
    preferences = list(preferences_collection.find())

    # Filter images liked by the user
    user_preferences = [p for p in preferences if p['user_id'] == user_id]
    liked_images = [p['image_id'] for p in user_preferences]

    # Create a dictionary to associate image IDs with tags
    image_tags = {item['filename']: ' '.join(item['image_tags']) for item in metadata}

    try:
        # Use a TfidfVectorizer to transform the tags into vectors
        vectorizer = TfidfVectorizer()
        image_vectors = vectorizer.fit_transform(image_tags.values())

        # Calculate similarities between images
        similarity_matrix = cosine_similarity(image_vectors)

        # Find indices of images liked by the user
        liked_image_indices = [list(image_tags.keys()).index(img_id) for img_id in liked_images]

        # Calculate recommendation scores for each image based on their similarity
        recommendation_scores = np.sum(similarity_matrix[liked_image_indices], axis=0)

        # Find indices of recommended images
        recommended_image_indices = np.argsort(recommendation_scores)[::-1]

        # Return the IDs of the recommended images
        recommended_image_ids = [list(image_tags.keys())[index] for index in recommended_image_indices]

        # Filter images already liked by the user
        recommended_image_ids = [img_id for img_id in recommended_image_ids if img_id not in liked_images]

    except ValueError as e:
        print(f"Error: {str(e)}")
        print("Returning an empty list of recommendations.")
        recommended_image_ids = []

    return recommended_image_ids[:10]


def collaborative_filtering_recommendation(user_id, db_collection_preferences, k=10):
    # Connect to the MongoDB client
    client = MongoClient("mongodb://mongo:27017/")
    db = client["image_db"]  # replace "mydatabase" with your database name

    # Charger les préférences des utilisateurs à partir de MongoDB
    preferences_collection = db[db_collection_preferences]
    preferences = list(preferences_collection.find())

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


def hybrid_recommendation(user_id, alpha=0.5, db_collection_metadata="metadata",
                          db_collection_preferences="preferences", k=10):
    content_based_recs = content_based_recommendation(user_id, db_collection_metadata, db_collection_preferences)
    collaborative_recs = collaborative_filtering_recommendation(user_id, db_collection_preferences, k)

    # Combiner les scores de recommandation des deux approches
    combined_scores = defaultdict(float)
    for i, image_id in enumerate(content_based_recs):
        combined_scores[image_id] += (1 - alpha) * (len(content_based_recs) - i)

    for i, image_id in enumerate(collaborative_recs):
        combined_scores[image_id] += alpha * (len(collaborative_recs) - i)

    # Trier les images en fonction de leur score de recommandation combiné
    recommended_image_ids = sorted(combined_scores, key=combined_scores.get, reverse=True)

    return recommended_image_ids[:10]


if __name__ == "__main__":
    # Connect to MongoDB
    client = MongoClient('mongodb://mongo:27017/')
    db = client['image_db']
    coll_metadata = db['metadata']
    coll_preferences = db['preferences']

    # Download the Unsplash dataset and images here
    # Add your own code

    # Extract metadata from the images
    input_dir = './bigdata_app/data/images/'
    extract_image_metadata(input_dir, coll_metadata)

    # Simuler les préférences des utilisateurs
    add_user_preference(1, 'liZpmbRG4WQ.jpg', coll_preferences)
    add_user_preference(1, 'FJc8DIDMGek.jpg', coll_preferences)
    add_user_preference(2, '4_Bc9CSm70A.jpg', coll_preferences)
    add_user_preference(2, '9CjgeMAM2SI.jpg', coll_preferences)
    add_user_preference(3, '731BXpcasJI.jpg', coll_preferences)
    add_user_preference(3, 'AMuKRdPBuek.jpg', coll_preferences)

    # Tester les recommandations basées sur le contenu
    content_recs = content_based_recommendation(1, coll_metadata, coll_preferences)
    print("Recommandations basées sur le contenu pour l'utilisateur 1:")
    print(content_recs)

    # Tester les recommandations par filtrage collaboratif
    collaborative_recs = collaborative_filtering_recommendation(1, coll_preferences)
    print("Recommandations par filtrage collaboratif pour l'utilisateur 1:")
    print(collaborative_recs)

    # Tester les recommandations hybrides
    hybrid_recs = hybrid_recommendation(1, db_collection_metadata=coll_metadata,
                                        db_collection_preferences=coll_preferences)
    print("Recommandations hybrides pour l'utilisateur 1:")
    print(hybrid_recs)