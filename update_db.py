import re
import numpy as np
from src.db_manager import get_connection

def actualizar_base_datos():
    print("Conectando a la base de datos...")
    conn = get_connection()
    cur = conn.cursor()

    # 1. Crear las nuevas columnas (Ignora el error si ya existen)
    try:
        cur.execute("ALTER TABLE matchups ADD COLUMN volatility_score REAL DEFAULT 0.0")
        cur.execute("ALTER TABLE matchups ADD COLUMN clean_razon TEXT")
        print("Columnas creadas con éxito.")
    except Exception as e:
        print("Las columnas ya existían (Omitiendo creación).")

    # 2. Leer todos los matchups
    cur.execute("SELECT own_hero_id, enemy_hero_id, enemy_position, razon FROM matchups")
    rows = cur.fetchall()
    
    print(f"Procesando {len(rows)} matchups...")

    for row in rows:
        own_id, enemy_id, pos, razon = row
        if not razon:
            continue

        sim_scores = []
        lines = str(razon).split('\n')
        clean_lines = []

        # Extraer los datos matemáticos y limpiar la basura vieja
        for line in lines:
            if "⚠️ ALERTA DE VOLATILIDAD" in line:
                continue # Omitimos la alerta vieja
                
            if "Simulación" in line:
                # Extraemos los números exactos de midgame y lategame
                valores = re.findall(r"(?:Midgame|Lategame):\s*([-+]?\d*\.?\d+)", line)
                if valores:
                    promedio_sim = np.mean([float(v) for v in valores])
                    sim_scores.append(promedio_sim)
                    
            clean_lines.append(line)

        texto_limpio = "\n".join(clean_lines).strip()
        sigma = round(float(np.std(sim_scores)), 2) if len(sim_scores) > 1 else 0.0

        # 3. Guardar los cálculos limpios en la base de datos
        cur.execute("""
            UPDATE matchups 
            SET volatility_score = ?, clean_razon = ? 
            WHERE own_hero_id = ? AND enemy_hero_id = ? AND enemy_position = ?
        """, (sigma, texto_limpio, own_id, enemy_id, pos))

    conn.commit()
    conn.close()
    print("¡Base de datos actualizada y purgada con éxito!")

if __name__ == "__main__":
    actualizar_base_datos()