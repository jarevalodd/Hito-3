#import os
#os.environ["PGCLIENTENCODING"] = "LATIN1"     # forzamos la decodificación correcta


from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import psycopg 

app = FastAPI()
templates = Jinja2Templates(directory="templates")

conn = psycopg.connect(
    host="localhost",
    dbname="Hito2",
    user="postgres",
    password="bigotes2020",
    application_name="fastapi_app"
)



@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/consulta1", response_class=HTMLResponse)
def get_consulta1(request: Request):
    return templates.TemplateResponse("consulta1.html", {"request": request, "resultados": None})

@app.post("/consulta1", response_class=HTMLResponse)
def post_consulta1(request: Request, año_inicio: int = Form(...), año_fin: int = Form(...), umbral: int = Form(...)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.track_name, al.album_release_date, c.popularity
            FROM cancion AS c
            JOIN album AS al ON c.album_uri = al.album_uri
            WHERE EXTRACT(YEAR FROM al.album_release_date) BETWEEN %s AND %s
            AND c.popularity > %s;
        """, (año_inicio, año_fin, umbral))
        resultados = cur.fetchall()
    return templates.TemplateResponse("consulta1.html", {"request": request, "resultados": resultados})

@app.get("/consulta2", response_class=HTMLResponse)
def consulta2(request: Request):
    with conn.cursor() as cur:
        cur.execute("""
            WITH top_tracks AS (
                SELECT LOWER(g.artist_genre) AS genero,
                       c.track_name,
                       c.popularity,
                       c.danceability,
                       ROW_NUMBER() OVER (
                           PARTITION BY LOWER(g.artist_genre)
                           ORDER BY c.popularity DESC, c.danceability DESC
                       ) AS rn
                FROM cancion c
                JOIN cancion_artista ca USING (track_uri)
                JOIN artista_genero ag USING (artist_uri)
                JOIN genero g USING (genero_id)
                WHERE LOWER(g.artist_genre) IN ('pop','rock','hip hop')
            )
            SELECT genero, track_name, popularity, danceability
            FROM top_tracks
            WHERE rn <= 5
            ORDER BY genero, popularity DESC;
        """)
        resultados = cur.fetchall()
    return templates.TemplateResponse("consulta2.html", {"request": request, "resultados": resultados})

@app.get("/consulta3", response_class=HTMLResponse)
def consulta3(request: Request):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT al.album_name, SUM(c.track_duration_ms) AS total_duracion_ms,
                   ROUND(AVG(c.popularity), 2) AS promedio_popularity
            FROM album AS al
            JOIN cancion AS c ON al.album_uri = c.album_uri
            GROUP BY al.album_uri, al.album_name
            ORDER BY total_duracion_ms DESC
            LIMIT 1;
        """)
        resultado = cur.fetchone()
    return templates.TemplateResponse("consulta3.html", {"request": request, "resultado": resultado})

@app.get("/consulta4", response_class=HTMLResponse)
def consulta4(request: Request):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT nombre, ROUND(valence_promedio, 3), album, pais, formacion
            FROM vista_top_artistas_valence
            ORDER BY valence_promedio DESC
            LIMIT 10;
        """)
        resultados = cur.fetchall()
    return templates.TemplateResponse("consulta4.html", {"request": request, "resultados": resultados})
