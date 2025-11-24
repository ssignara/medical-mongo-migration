import os
import pytest
from pymongo import MongoClient
from src.migration.migration import build_mongo_uri


def test_build_mongo_uri_with_argument():
    uri = build_mongo_uri("mongodb://root:pass@localhost:27017/?authSource=admin")
    assert uri == "mongodb://root:pass@localhost:27017/?authSource=admin"


def test_build_mongo_uri_from_env(monkeypatch):
    monkeypatch.setenv("MONGO_INITDB_ROOT_USERNAME", "root")
    monkeypatch.setenv("MONGO_INITDB_ROOT_PASSWORD", "rootpassword")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")

    uri = build_mongo_uri(None)

    assert uri == "mongodb://root:rootpassword@localhost:27017/?authSource=admin"


def test_build_mongo_uri_missing_env(monkeypatch):
    monkeypatch.delenv("MONGO_INITDB_ROOT_USERNAME", raising=False)
    monkeypatch.delenv("MONGO_INITDB_ROOT_PASSWORD", raising=False)
    monkeypatch.delenv("MONGO_HOST", raising=False)
    monkeypatch.delenv("MONGO_PORT", raising=False)

    with pytest.raises(ValueError):
        build_mongo_uri(None)
