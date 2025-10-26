import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='backend/.env')

MONGODB_URL = os.getenv("MONGODB_URL")
