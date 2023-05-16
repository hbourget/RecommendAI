# python/Dockerfile
# Utilisation d'une image de base plus récente (si disponible)
FROM python:3.11-slim

# Passage au répertoire de travail /app
WORKDIR /app

# Ajout du fichier requirements.txt au conteneur
COPY requirements.txt .

# Utilisation de --no-cache-dir pour une image Docker plus petite
# Ajout de --upgrade pour s'assurer que les paquets sont à jour
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Ajout du fichier function.py au conteneur
COPY function.py .

# Définition de la commande à exécuter lors de l'exécution du conteneur
CMD ["python", "function.py"]