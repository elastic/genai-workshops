import logging
import os
import requests
from io import StringIO
from dotenv import load_dotenv

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Now load environment variables
def load_env():
    try:
        response = requests.get('http://kubernetes-vm:9000/env')
        response.raise_for_status()
        load_dotenv(stream=StringIO(response.text))
        logging.debug("Environment variables loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load environment variables: {e}")

load_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import search_router
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(ElasticAPM, client=apm)

# Include the router
app.include_router(search_router.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

