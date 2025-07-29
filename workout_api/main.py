# Em workout_api/main.py
from fastapi import FastAPI
from fastapi_pagination import add_pagination # Importar
from workout_api.routers import api_router

app = FastAPI(title='WorkoutApi')
app.include_router(api_router)
add_pagination(app) # Adicionar esta linha