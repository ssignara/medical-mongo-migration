#!/usr/bin/env python3
"""
Script de migration : CSV -> MongoDB, avec logging et contrôle post-insertion.

✅ Peut être utilisé :
    - en local, en ligne de commande
    - dans Docker, avec des variables d'environnement

Priorité de configuration :
    1. Arguments de la ligne de commande
    2. Variables d'environnement Docker
    3. Valeurs par défaut internes
"""

import argparse
import sys
import os
import logging

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, ServerSelectionTimeoutError


# =========================
#       CONFIG LOGGING
# =========================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "migration.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)


# =========================
#       FONCTIONS
# =========================

from typing import Optional

def build_mongo_uri(cli_uri: Optional[str]) -> str:

    """
    Construit l'URI MongoDB en respectant cet ordre :
    1) URI passée en argument --uri
    2) Variable d'environnement MONGO_URI
    3) Construction à partir de MONGO_USER / MONGO_PASSWORD / MONGO_HOST / MONGO_PORT
    4) Fallback : mongodb://mongodb:27017
    """
    if cli_uri:
        logging.info("Utilisation de l'URI MongoDB fournie en argument.")
        return cli_uri

    env_uri = os.getenv("MONGO_URI")
    if env_uri:
        logging.info("Utilisation de l'URI MongoDB provenant de MONGO_URI.")
        return env_uri

    host = os.getenv("MONGO_HOST", "mongodb")
    port = os.getenv("MONGO_PORT", "27017")
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASSWORD")
    auth_db = os.getenv("MONGO_AUTH_DB", "admin")

    if user and password:
        logging.info("Construction de l'URI MongoDB à partir des variables MONGO_USER/PASSWORD/HOST/PORT.")
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource={auth_db}"

    logging.info("Construction de l'URI MongoDB sans authentification.")
    return f"mongodb://{host}:{port}"


def main():
    # =========================
    #       ARGUMENTS CLI
    # =========================
    parser = argparse.ArgumentParser(
        description="Importer un CSV dans MongoDB (avec logging et vérification)."
    )

    parser.add_argument(
        "--csv",
        default=os.getenv("CSV_PATH", "data/healthcare_dataset.csv"),
        help="Chemin du CSV (défaut : data/healthcare_dataset.csv)",
    )
    parser.add_argument(
        "--uri",
        default=None,
        help="URI MongoDB complète (sinon construite via variables d'environnement).",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("MONGO_DB", "medical_db"),
        help="Nom de la base (défaut : medical_db)",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("MONGO_COLLECTION", "patients"),
        help="Nom de la collection (défaut : patients)",
    )

    args = parser.parse_args()

    csv_path = args.csv
    mongo_uri = build_mongo_uri(args.uri)
    db_name = args.db
    collection_name = args.collection

    logging.info("=== DÉBUT DE LA MIGRATION CSV -> MongoDB ===")
    logging.info(f"CSV       : {csv_path}")
    logging.info(f"Mongo URI : {mongo_uri}")
    logging.info(f"Base      : {db_name}")
    logging.info(f"Collection: {collection_name}")

    # =========================
    #       1) LECTURE CSV
    # =========================
    try:
        df = pd.read_csv(csv_path)  # ajouter sep=";" si ton CSV est séparé par des ';'
        nb_csv = len(df)
        if nb_csv == 0:
            logging.warning(f"Le CSV '{csv_path}' est vide (0 ligne de données).")
        logging.info(f"CSV chargé avec succès : {nb_csv} lignes (hors entête).")
    except FileNotFoundError:
        logging.error(f"Fichier introuvable : {csv_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erreur de lecture du CSV : {e}")
        sys.exit(1)

    # =========================
    #       2) CONNEXION MONGO
    # =========================
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")  # test rapide
        coll = client[db_name][collection_name]
        logging.info(
            f"Connexion réussie à MongoDB, base '{db_name}', collection '{collection_name}'."
        )
    except ServerSelectionTimeoutError as e:
        logging.error(f"Impossible de se connecter à MongoDB (timeout) : {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erreur de connexion MongoDB : {e}")
        sys.exit(1)

    # =========================
    #   3) RÉINITIALISATION
    # =========================
    coll.drop()
    logging.info("Collection supprimée avant nouvel import (drop).")

    # =========================
    #       4) INSERTION
    # =========================
    docs = df.to_dict(orient="records")

    try:
        if docs:
            coll.insert_many(docs, ordered=False)
            logging.info(f"{len(docs)} documents insérés dans MongoDB.")
        else:
            logging.warning("Aucun document à insérer (CSV vide).")
    except BulkWriteError as e:
        logging.error("Erreur d'écriture (peut-être un doublon sur _id ou un index unique).")
        logging.error(e.details)
        sys.exit(1)
    except Exception as e:
        logging.error(f"Erreur d'insertion : {e}")
        sys.exit(1)

    # =========================
    #   5) CONTRÔLE FINAL
    # =========================
    nb_db = coll.count_documents({})
    logging.info(f"Documents présents dans la base : {nb_db}")

    if nb_db == len(df):
        logging.info("✅ Vérification OK : le nombre de documents correspond au nombre de lignes du CSV.")
        logging.info("=== MIGRATION TERMINÉE AVEC SUCCÈS ===")
        sys.exit(0)
    else:
        logging.warning("⚠️ Décalage détecté entre CSV et MongoDB.")
        logging.warning("=== MIGRATION TERMINÉE AVEC INCOHÉRENCE ===")
        sys.exit(2)


if __name__ == "__main__":
    main()
