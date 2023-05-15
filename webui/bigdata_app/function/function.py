import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from pymongo import MongoClient

input_file = '/data/unsplash-research-dataset-lite-latest/photos.tsv000'
output_dir = '/data/images/'
url = 'https://unsplash.com/data/lite/latest'
zip_file = '/data/unsplash-research-dataset-lite-latest.zip'
extract_dir = '/data/unsplash-research-dataset-lite-latest'


def add_user_preference(user_id, image_id, db_collection):
    # Connect to the MongoDB client
    client = MongoClient("mongodb://localhost:27017/")
    db = client["image_db"]
    collection = db[db_collection]

    preference = {'user_id': user_id, 'image_id': image_id}
    collection.insert_one(preference)


def content_based_recommendation(user_id, db_collection_metadata, db_collection_preferences):
    # Connect to the MongoDB client
    client = MongoClient("mongodb://localhost:27017/")
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
    client = MongoClient("mongodb://localhost:27017/")
    db = client["image_db"]

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
    client = MongoClient('mongodb://localhost:27017/')
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
