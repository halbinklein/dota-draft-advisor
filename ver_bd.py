from src.db_manager import get_connection

def escanear_bd():
    conn = get_connection()
    cur = conn.cursor()
    
    # Buscamos exactamente el enfrentamiento de tus imágenes
    cur.execute('''
        SELECT m.razon 
        FROM matchups m 
        JOIN heroes h1 ON m.own_hero_id = h1.hero_id 
        JOIN heroes h2 ON m.enemy_hero_id = h2.hero_id 
        WHERE h1.name = 'Faceless Void' AND h2.name = 'Axe'
    ''')
    
    row = cur.fetchone()
    if row:
        print("\n=== COPIA Y PEGA TODO EL TEXTO DE ABAJO EN EL CHAT ===")
        # repr() nos muestra la "Matrix" (los saltos de línea \n y caracteres ocultos)
        print(repr(row[0]))
        print("====================================================\n")
    else:
        print("No se encontró el matchup en la base de datos.")

if __name__ == "__main__":
    escanear_bd()