import re
import numpy as np
from src.db_manager import get_connection

def actualizar_base_datos():
    print("Conectando a la base de datos...")
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE matchups ADD COLUMN volatility_score REAL DEFAULT 0.0")
        cur.execute("ALTER TABLE matchups ADD COLUMN clean_razon TEXT")
        print("Nuevas columnas creadas.")
    except:
        print("Las columnas ya existen.")

    cur.execute("SELECT own_hero_id, enemy_hero_id, enemy_position, razon FROM matchups")
    rows = cur.fetchall()

    for row in rows:
        own_id, enemy_id, pos, razon = row
        if not razon:
            continue

        # 1. Extraer puntajes ignorando el HTML
        sim_scores = []
        # Busca todo lo que esté después de "Simulación X:" y antes de cerrar la etiqueta HTML
        sims = re.findall(r'Simulación \d+:([^<]+)', str(razon))
        
        for sim in sims:
            # Saca todos los números decimales o enteros de esa línea
            valores = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', sim)
            if valores:
                sim_scores.append(np.mean([float(v) for v in valores]))
        
        # Calcular Desviación Estándar (sigma)
        sigma = round(float(np.std(sim_scores)), 2) if len(sim_scores) > 1 else 0.0

        # 2. Borrar SÓLO la alerta vieja (con sus asteriscos y saltos de línea ocultos)
        texto_limpio = re.sub(r'(\n|<br>|\s)*⚠️\s*\*\*ALERTA DE VOLATILIDAD:\*\*.*?(?=<br>|<details>|\Z)', '', str(razon), flags=re.DOTALL)

        # 3. Guardar en la Base de Datos
        cur.execute("""
            UPDATE matchups 
            SET volatility_score = ?, clean_razon = ? 
            WHERE own_hero_id = ? AND enemy_hero_id = ? AND enemy_position = ?
        """, (sigma, texto_limpio, own_id, enemy_id, pos))

    conn.commit()
    conn.close()
    print("¡Base de datos actualizada, HTML superado y purgada con éxito!")

if __name__ == "__main__":
    actualizar_base_datos()