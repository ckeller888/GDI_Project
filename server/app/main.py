from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.responses import ORJSONResponse

# CORS aktivieren für FastAPI Backend
from fastapi.middleware.cors import CORSMiddleware

# Datenbank Verbindung
from psycopg2 import pool

# from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import json
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv

app = FastAPI()

# CORS Einstellungen
# siehe: https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple Hello World example
@app.get("/")
async def root():
    return {"message": "Hello GDI Project"}


# Erstellt eine About Seite mit HTML Output
# import HTMLResponse benötigt
@app.get("/about/")
def about():
    return HTMLResponse(
        """
    <html>
      <head>
        <title>FAST API Service</title>
      </head>
      <body>
        <div align="center">
          <h1>Simple FastAPI Server About Page</h1>
          <p>Dieser FastAPI Rest Server bietet eine einfache REST Schnittstelle. Die Dokumentation ist über <a href="http://localhost:8000/docs">http://localhost:8000/docs</a> verfügbar.</p> 
        </div>
      </body>
    </html>
    """
    )


# Simple static JSON Response
# (requires package "orjson" https://github.com/ijl/orjson https://anaconda.org/conda-forge/orjson conda install -c conda-forge orjson)
# source: https://fastapi.tiangolo.com/advanced/custom-response/
@app.get("/points/", response_class=ORJSONResponse)
async def read_points():
    return ORJSONResponse(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "FHNW"},
                    "geometry": {
                        "coordinates": [7.642053725874888, 47.53482543914882],
                        "type": "Point",
                    },
                    "id": 0,
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Bern"},
                    "geometry": {
                        "coordinates": [7.4469686824532175, 46.95873550880529],
                        "type": "Point",
                    },
                    "id": 1,
                },
                {
                    "type": "Feature",
                    "properties": {"name": "Zurich"},
                    "geometry": {
                        "coordinates": [8.54175132796243, 47.37668053625666],
                        "type": "Point",
                    },
                    "id": 2,
                },
            ],
        }
    )


# Post Query - test on the OPENAPI Docs Page
@app.post("/square")
def square(some_number: int) -> dict:
    square = some_number**2
    return {f"{some_number} squared is: ": square}


load_dotenv()

# Datenbankverbindung
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "FotoPoints"
DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_POOL_MIN_CONN = 1
DB_POOL_MAX_CONN = 10

db_pool = pool.SimpleConnectionPool(
    DB_POOL_MIN_CONN,
    DB_POOL_MAX_CONN,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)


# Antwortschema
class PunkteResponse(BaseModel):
    id: int
    name: str
    datum: str | None = None
    besucht: str
    x: float
    y: float
    geom: str


logging.basicConfig(level=logging.INFO)


@app.get("/getPoints")
async def get_points_geojson():
    conn = None
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()
        query = """
            SELECT 
            id, 
            name, 
            datum,
            CASE besucht
                WHEN 1 THEN 'ja'
                ELSE 'nein'
            END as besucht,
            foto,
            ST_AsGeoJSON(ST_Force2D(geom)) as geom,
            bemerkungen,
            adresse,
            infos
        FROM fotopoints
        """

        cur.execute(query)
        results = cur.fetchall()
        features = []
        for row in results:
            datum = row[2]
            datum_formatted = datum.strftime("%d.%m.%Y") if datum else None

            # Extrahiere nur den Pfad ab /fotos/ (damit es im Frontend funktioniert)
            foto_path = row[4] or ""
            relative_url = None
            if foto_path:
                filename = foto_path.replace("\\", "/").split("/")[-1]  # nur Dateiname
                relative_url = f"/fotos/{filename}"

            features.append(
                {
                    "type": "Feature",
                    "id": row[0],
                    "geometry": json.loads(row[5]),
                    "properties": {
                        "id": row[0],
                        "name": row[1],
                        "datum": datum_formatted,
                        "besucht": row[3],
                        "foto": relative_url,
                        "bemerkungen": row[6],
                        "adresse": row[7],
                        "infos": row[8],
                    },
                }
            )
        return JSONResponse({"type": "FeatureCollection", "features": features})
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            db_pool.putconn(conn)
