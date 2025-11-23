from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

# Chargement des variables d'environnement (.env ou variables Docker)
load_dotenv()

# URL MongoDB (doit matcher ton docker-compose : service "mongodb")
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("❌ Variable d'environnement MONGO_URI manquante")

# Connexion MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Petit ping pour vérifier la connexion
    client.admin.command("ping")
except Exception as e:
    raise RuntimeError(f"❌ Impossible de se connecter à MongoDB : {e}")

db = client["medical_db"]
patients_col = db["patients"]

# ⚠️ C'est CET objet que uvicorn cherche : api.main:app
app = FastAPI(title="Medical API", version="1.0.0")


# ---------- Utilitaires ----------

def serialize_patient(doc: dict) -> dict:
    """Convertit l'_id MongoDB en string pour JSON."""
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"])
    return doc


# ---------- Endpoints ----------

@app.get("/")
def root():
    """Endpoint de santé simple."""
    return {"message": "Medical API is running 🚑"}


@app.get("/patients")
def list_patients(skip: int = 0, limit: int = 20):
    """
    Liste paginée des patients.
    - skip : nombre de documents à ignorer
    - limit : nombre maximum de documents retournés
    """
    cursor = patients_col.find().skip(skip).limit(limit)
    patients = [serialize_patient(d) for d in cursor]
    return {"count": len(patients), "patients": patients}


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    """
    Récupère un patient par son _id MongoDB.
    """
    try:
        oid = ObjectId(patient_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")

    patient = patients_col.find_one({"_id": oid})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    return serialize_patient(patient)


@app.get("/stats/patients-by-hospital")
def patients_by_hospital():
    """
    Retourne le nombre de patients par hôpital.
    ⚠️ Le champ utilisé dans MongoDB est 'Hospital' (avec H majuscule).
    """
    pipeline = [
        {"$group": {"_id": "$Hospital", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]

    result = list(patients_col.aggregate(pipeline))
    stats = [{"hospital": r["_id"], "total": r["total"]} for r in result]
    return {"stats": stats}
