import os
from dotenv import load_dotenv
from psycopg2 import pool, Binary
import psycopg2
from datetime import datetime

load_dotenv()


origins = [
    "*",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
]


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


def update_fotopoint(
    gid: int,
    datum: str = None,
    besucht: int = None,
    bild_pfad: str = None,
    bemerkungen: str = None,
    adresse: str = None,
    infos: str = None,
):
    """
    Aktualisiert Datum, besucht und optional das Bild.
    """
    conn = None
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()

        updates = []
        params = []

        if datum is not None:
            datum_obj = datetime.strptime(datum, "%Y-%m-%d").date()
            updates.append("datum = %s")
            params.append(datum_obj)

        if besucht is not None:
            updates.append("besucht = %s")
            params.append(besucht)

        if bild_pfad is not None:
            # Optional: überprüfe, ob Datei existiert
            abs_pfad = os.path.abspath(bild_pfad)
            if not os.path.exists(abs_pfad):
                print(f"Bild existiert nicht: {abs_pfad}, nur Pfad wird gespeichert.")
            # Speichern des Pfads als String
            updates.append("foto = %s")
            params.append(bild_pfad)

        if bemerkungen is not None:
            updates.append("bemerkungen = %s")
            params.append(bemerkungen)

        if adresse is not None:
            updates.append("adresse = %s")
            params.append(adresse)

        if infos is not None:
            updates.append("infos = %s")
            params.append(infos)

        if not updates:
            print("Keine Werte zum Aktualisieren übergeben.")
            return

        sql = f"""
        UPDATE public.fotopoints
        SET {", ".join(updates)}
        WHERE gid = %s
        """
        params.append(gid)

        cur.execute(sql, params)
        conn.commit()

        if cur.rowcount > 0:
            print(f"Eintrag mit gid {gid} erfolgreich aktualisiert.")
        else:
            print(f"Kein Eintrag mit gid {gid} gefunden.")

    except Exception as e:
        if conn:
            conn.rollback()
        print("Fehler beim Aktualisieren:", e)
    finally:
        if conn:
            db_pool.putconn(conn)


# Beispielaufruf
# update_fotopoint(4, "2024-08-16", 1, "client/public/fotos/Heidihaus.jpeg")
# oder nur etwas updaten: update_fotopoint(4, datum ="2024-08-16", besucht = 1, bild_pfad= "client/public/fotos/Heidihaus.jpeg", bemerkungen = "", adresse = "",infos = "")

# update_fotopoint(3, bild_pfad="client/public/fotos/Hallwyl.jpg")
# update_fotopoint(
#     52,
#     bemerkungen="""Fotopoint kann man drehen.
#     Zweites Foto Richtung Meilen: client/public/fotos/Meilen_2.jpg""",
# )


update_fotopoint(
    87,
    name="",
    besucht=0,
    adresse="""Lindt Home of Chocolate, Schokoladenplatz 1, 8802 Kilchberg 
    Parking: Lindt Home of Chocolate Parking, Seestrasse 204, 8802 Kilchberg
    Fussweg: 1 Minute""",
    infos="""Das Lindt Home of Chocolate ist eine einzigartige Besucherattraktion auf dem Gelände der historischen Schokoladenfabrik von Lindt & Sprüngli. Das für die Schweiz wichtige kulturelle Gut der Schokolade, wird hier seit 1899 hergestellt und kann im Lindt Home of Chocolate hautnah erlebt werden. Zudem begeistert das Gebäude durch eine spektakuläre Architektur. Es wurde von den berühmten Schweizer Architekten Christ & Gantenbein entworfen.""",
)
