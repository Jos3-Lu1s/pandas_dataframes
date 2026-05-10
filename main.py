import pandas as pd
from pathlib import Path

def unificar_csvs():
    # Rutas de las carpetas
    raw_dir = Path("data/raw")
    filtered_dir = Path("data/filtered")
    output_file = filtered_dir / "datos_filtrados.csv"

    # Crear la carpeta filtered si no existe
    filtered_dir.mkdir(parents=True, exist_ok=True)

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
            df = pd.read_csv(f, low_memory=False, encoding="latin-1")
            
            # Filtrar por ENTIDAD_RES == 21 o ENTIDAD_NAC == 21
            df = df[(df["ENTIDAD_RES"] == 21) | (df["ENTIDAD_NAC"] == 21)]
            
            # Reparar codificación de PAIS_NACIONALIDAD
            if "PAIS_NACIONALIDAD" in df.columns:
                df["PAIS_NACIONALIDAD"] = (
                    df["PAIS_NACIONALIDAD"]
                    .astype(str)
                    .str.encode("latin1")
                    .str.decode("utf-8")
                )

            # Añadir una columna con el nombre del archivo original
            df['ARCHIVO_ORIGEN'] = f.name
            dfs.append(df)
            print(f"Cargado y filtrado: {f.name}")
        except Exception as e:
            print(f"Error al leer {f.name}: {e}")

    if dfs:
        # Unificar
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Guardar en la carpeta filtered
        df_final.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\nÉxito: Archivo filtrado y unificado guardado en {output_file}")
        print(f"Total de filas filtradas: {len(df_final)}")
    else:
        print("No se pudo procesar ningún archivo o no hubo coincidencias con el filtro.")

if __name__ == "__main__":
    unificar_csvs()
