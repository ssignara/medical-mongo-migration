import os
import sys
from types import SimpleNamespace

import pandas as pd
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_MIGRATION_DIR = ROOT_DIR / "src" / "migration"

if str(SRC_MIGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_MIGRATION_DIR))
    
import migration


# ==============================
#   TESTS SUR build_mongo_uri
# ==============================

def test_build_mongo_uri_priorite_argument_cli(monkeypatch):
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGO_USER", raising=False)
    monkeypatch.delenv("MONGO_PASSWORD", raising=False)
    monkeypatch.delenv("MONGO_HOST", raising=False)
    monkeypatch.delenv("MONGO_PORT", raising=False)

    cli_uri = "mongodb://user:pass@host:27017/?authSource=admin"
    result = migration.build_mongo_uri(cli_uri)

    assert result == cli_uri


def test_build_mongo_uri_depuis_variables_d_environnement(monkeypatch):
    monkeypatch.setenv("MONGO_USER", "root")
    monkeypatch.setenv("MONGO_PASSWORD", "rootpassword")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")

    result = migration.build_mongo_uri(None)

    assert result.startswith("mongodb://root:rootpassword@localhost:27017/")
    assert "authSource=admin" in result


# ==============================
#   TEST DU FLUX COMPLET main()
# ==============================

class FakeCollection:
    def __init__(self):
        self.docs = []

    def drop(self):
        self.docs.clear()

    def insert_many(self, docs, ordered=False):
        self.docs.extend(docs)

    def count_documents(self, _filter=None):
        return len(self.docs)


class FakeDB(dict):
    def __getitem__(self, name):
        if name not in self:
            self[name] = FakeCollection()
        return dict.__getitem__(self, name)


class FakeClient:
    def __init__(self, uri, serverSelectionTimeoutMS=5000):
        self.uri = uri
        self.admin = SimpleNamespace(command=lambda cmd: None)
        self._dbs = {}

    def __getitem__(self, dbname):
        if dbname not in self._dbs:
            self._dbs[dbname] = FakeDB()
        return self._dbs[dbname]


def test_main_migration_complete_sans_vraie_base(monkeypatch, tmp_path):
    monkeypatch.setattr(migration, "MongoClient", FakeClient)

    fake_df = pd.DataFrame(
        [
            {"patient_id": 1, "age": 35, "hospital": "A"},
            {"patient_id": 2, "age": 50, "hospital": "B"},
        ]
    )

    def fake_read_csv(path):
        return fake_df

    monkeypatch.setattr(migration, "pd", SimpleNamespace(read_csv=fake_read_csv))

    csv_path = tmp_path / "dummy.csv"
    csv_path.write_text("dummy;file\n")

    test_argv = [
        "migration.py",
        "--csv",
        str(csv_path),
        "--uri",
        "mongodb://root:rootpassword@localhost:27017/?authSource=admin",
        "--db",
        "medical_db",
        "--collection",
        "patients",
    ]

    monkeypatch.setattr(sys, "argv", test_argv)

    with pytest.raises(SystemExit) as exc_info:
        migration.main()

    assert exc_info.value.code == 0
