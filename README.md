📘 README – Migration des données CSV vers MongoDB

Projet : Importation automatisée du dataset médical dans une base NoSQL

🎯 Introduction

Dans ce projet, l’objectif est d’automatiser la migration des données médicales du client vers MongoDB, afin d’améliorer la scalabilité et la performance de leur système.

Pour cela, nous utilisons :

un script Python de migration

une architecture Docker pour garantir la portabilité

des logs pour assurer la traçabilité

une vérification automatique de la cohérence des données

Ce README explique le fonctionnement du script de migration, sa logique interne, et comment l’exécuter.

🏗️ 1. Architecture générale

La migration repose sur 3 éléments principaux :

🔹 1. Le dataset CSV

Contient les données médicales à importer.

🔹 2. Le script migration.py

Il lit le CSV, se connecte à MongoDB, insère les données puis vérifie la cohérence.

🔹 3. Docker Compose

Permet d’exécuter MongoDB et le script dans des conteneurs indépendants.

🔍 2. Logique du script de migration

Le script migration.py a été conçu pour être :

simple

sécurisé

robuste

compatible Docker

Il suit 5 grandes étapes.

2.1 — Lecture du CSV

Le script commence par charger le fichier CSV à l’aide de pandas :

df = pd.read_csv(csv_path)


Il récupère aussi :

le nombre de lignes dans le fichier

les colonnes disponibles

Cette étape permet de préparer les données avant insertion.

2.2 — Construction de l’URI MongoDB

Le script peut obtenir l’adresse MongoDB de différentes façons :

via un argument CLI (--uri)

via une variable d’environnement (MONGO_URI)

via les variables :

MONGO_USER
MONGO_PASSWORD
MONGO_HOST
MONGO_PORT


sinon, il utilise mongodb://mongodb:27017

Cette flexibilité permet :

l’utilisation en local

l’utilisation dans Docker

l’utilisation sur un serveur distant

2.3 — Connexion à MongoDB

Une fois l’URI construite, le script tente de se connecter :

client.admin.command("ping")


Cette commande permet :

de vérifier la connexion

de détecter les erreurs rapidement

d’éviter une insertion partielle ou corrompue

Si MongoDB ne répond pas → le script s’arrête.

2.4 — Réinitialisation et insertion des données

Pour garantir une base propre :

coll.drop()


Ensuite, chaque ligne du CSV est insérée comme un document JSON :

docs = df.to_dict(orient="records")
coll.insert_many(docs, ordered=False)


Cela permet :

une migration complète

sans doublons

reproductible à chaque exécution

2.5 — Vérification de cohérence

À la fin, le script compte les documents réellement insérés dans MongoDB :

nb_db = coll.count_documents({})


Puis compare avec le nombre de lignes du CSV.

✔️ Si c’est identique → migration réussie
⚠️ Sinon → incohérence détectée

Cette étape sécurise totalement le processus d’import.

📝 3. Logs d'exécution

Tous les événements importants (connexion, insertion, erreurs…) sont enregistrés automatiquement dans :

logs/migration.log


Ce fichier permet :

de garder une trace des migrations

de faciliter le débogage

d’assurer une bonne observabilité

▶️ 4. Comment exécuter la migration
Option A — En local (hors Docker)
python migration.py \
    --csv data/healthcare_dataset.csv \
    --uri mongodb://localhost:27017 \
    --db medical_db \
    --collection patients

Option B — Via Docker Compose (recommandé)

Le script est exécuté automatiquement dans le conteneur migration.

Construire et lancer les services :

docker compose up --build


Le script s’exécutera et affichera la progression dans les logs.

📦 5. Variables d’environnement prises en charge

Le script peut utiliser les variables suivantes :

Variable	Rôle
CSV_PATH	Chemin du fichier CSV
MONGO_URI	URI complète MongoDB
MONGO_HOST	Host MongoDB
MONGO_PORT	Port (ex : 27017)
MONGO_USER	Nom d’utilisateur
MONGO_PASSWORD	Mot de passe
MONGO_DB	Nom de la base
MONGO_COLLECTION	Nom de la collection

🔐 6. Architecture de Sécurité – Gestion des Rôles MongoDB

Afin de garantir la sécurité et la bonne gouvernance des données de santé, trois rôles ont été définis autour de la base MongoDB.
Chaque rôle possède un niveau d’accès strictement limité selon le principe du moindre privilège.

👑 a) Administrateur — admin

Objectif : Gestion complète de la base de données
Permissions principales :

Accès total à toutes les bases

Création, suppression et modification des utilisateurs

Configuration générale de MongoDB

Gestion des rôles et permissions

Sauvegardes et restauration (backups)

👉 Utilisé exclusivement pour l'administration système, jamais pour exécuter la migration ou l’application.

🛠 b) Application métier — healthcare_app

Objectif : Accès opérationnel pour l’application Healthcare
Permissions principales :

Lecture / écriture sur la base medical_db

Gestion des données patients

Opérations CRUD complètes sur la collection patients

👉 Ce rôle n’a aucun accès administratif, seulement ce qui est nécessaire au fonctionnement de l’API.

📊 c) Analyste — healthcare_analyst

Objectif : Consultation et analyse
Permissions principales :

Lecture seule sur la base

Exécution de requêtes analytiques

Génération de rapports

👉 Ce rôle garantit qu’un analyste ne peut jamais modifier les données.

✔️ 7. Ce que garantit ce script
Fonctionnalité	Description
Automatisation	Import complet sans intervention
Robustesse	Gestion d’erreurs et vérifications
Cohérence	Comparaison CSV ↔ Mongo
Traçabilité	Tous les événements sont loggés
Portabilité	Compatible local / Docker / serveur
🏁 Conclusion

Ce système de migration permet d’importer le dataset médical du client de manière fiable, automatique et reproductible.
Il constitue une base solide pour :

la mise en place d’une API

l’analyse des données

l’intégration dans une architecture Big Data scalable

