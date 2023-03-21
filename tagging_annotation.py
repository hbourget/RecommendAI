import os
import csv
import nltk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from skimage.segmentation import slic

# Extraction des métadonnées des images à partir des fichiers TSV
data = []
for file in os.listdir("unsplash-research-dataset-lite-latest"):
    if file.endswith("photos.tsv000"):
        with open(os.path.join("unsplash-research-dataset-lite-latest", file), "r", encoding="utf8") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                data.append(row)

# Utilisation de modèles de NLP pour extraire des mots-clés et des entités pertinentes à partir des descriptions ou des légendes de chaque image
vectorizer = CountVectorizer(stop_words='english', max_df=0.95, min_df=2, max_features=1000)
X = vectorizer.fit_transform([row[1] for row in data])
lda = LatentDirichletAllocation(n_components=10, max_iter=5, learning_method='online', learning_offset=50., random_state=0)
lda.fit(X)
topic_word = lda.components_
vocab = vectorizer.get_feature_names()

# Utilisation de modèles d'apprentissage automatique pour classifier les images en fonction de leur contenu
X = np.array([np.array(Image.open(os.path.join("images", row[0] + ".jpg")).resize((128, 128))) for row in data])
X = np.reshape(X, (X.shape[0], -1))
kmeans = KMeans(n_clusters=10, random_state=0).fit(X)
labels = kmeans.labels_

# Utilisation d'algorithmes de segmentation d'image pour diviser chaque image en régions homogènes en termes de couleur et de texture
segments = []
for i in range(len(data)):
    image = np.array(Image.open(os.path.join("images", data[i][0] + ".jpg")))
    segments.append(slic(image, n_segments=100, compactness=10, sigma=1))

# Utilisation d'algorithmes de clustering pour regrouper les pixels en clusters de couleurs similaires et déterminer les couleurs prédominantes de chaque image
colors = []
for i in range(len(data)):
    image = np.array(Image.open(os.path.join("images", data[i][0] + ".jpg")))
    for j in range(len(np.unique(segments[i]))):
        mask = segments[i] == j
        cluster = image[mask]
        if len(cluster) > 0:
            color = np.mean(cluster, axis=0)
            colors.append(color)
colors = np.array(colors)
kmeans = KMeans(n_clusters=10, random_state=0).fit(colors)
color_labels = kmeans.labels_

# Enregistrement des tags et des informations de couleurs prédominantes dans un fichier TSV
df = pd.DataFrame(data, columns=["id", "description"])
df["topic"] = [np.argmax(topic_word[:,vectorizer.vocabulary_[word]]) for word in df["description"]]
df["label"] = labels
df["color_label"] = color_labels
df.to_csv("image_tags.tsv", sep='\t', index=False)
