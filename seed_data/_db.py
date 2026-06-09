"""Shared Mongo connection helper for the seed scripts."""

import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DB_NAME = "fanzone"


def get_db():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("MONGODB_URI is not set — populate .env before seeding.")
    return MongoClient(uri)[DB_NAME]
