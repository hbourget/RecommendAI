## RecommendAI, mise en place d'un [système de recommandation](https://en.wikipedia.org/wiki/Recommender_system)

### Fonctionnement & Installation

- `git clone https://github.com/hbourget/RecommendAI.git`
- `cd RecommendAI`
- `pip install -r requirements.txt`
- `cd bigdata`
- `python manage.py runserver`



- L'application est disponible sur `localhost:8000`
- Elle est composée de 3 pages :
  - La page d'authentification
  - La page d'accueil / recommendation

<u>Page d'accueil sans le dataset :</u>
<div style="weight:50%">

![Interface graphique 1](docs/interface1.png)
</div>

<u>Page d'acceuil avec le dataset deja telechargé :</u>
<div style="weight:50%">

![Interface graphique 2](docs/interface2.png)
</div>

Si le dataset est deja téléchargé, il sera détecté automatiquement. On peut ensuite commencer a aimer ou non les images aléatoirement proposées afin d'entrainer le modèle. A force d'utilisation, ce dernier sera de plus en plus précis et les images proposées seront de plus pertinentes en fonction des choix de l'utilisateur.
