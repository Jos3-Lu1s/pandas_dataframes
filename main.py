import pandas as pd
from pathlib import Path

def unificar_csvs():
    # Rutas de las carpetas
    raw_dir = Path("data/raw")
    merged_dir = Path("data/merged")
    output_file = merged_dir / "datos_unificados.csv"

    # Crear la carpeta merged si no existe
    merged_dir.mkdir(parents=True, exist_ok=True)

    # Buscar todos los archivos .csv en data/raw
    csv_files = list(raw_dir.glob("*.csv"))

    if not csv_files:
        print("No se encontraron archivos CSV en data/raw.")
        return

    print(f"Archivos encontrados: {[f.name for f in csv_files]}")

    # Leer y concatenar todos los archivos
    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, low_memory=False)
            # Opcional: añadir una columna con el nombre del archivo original
            df['ARCHIVO_ORIGEN'] = f.name
            dfs.append(df)
            print(f"Cargado: {f.name}")
        except Exception as e:
            print(f"Error al leer {f.name}: {e}")

    if dfs:
        # Unificar
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Guardar en la carpeta merged
        df_final.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\nÉxito: Archivo unificado guardado en {output_file}")
        print(f"Total de filas: {len(df_final)}")
    else:
        print("No se pudo procesar ningún archivo.")

if __name__ == "__main__":
    unificar_csvs()
