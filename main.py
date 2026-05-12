import pandas as pd
from pathlib import Path

def unificar_csvs():
    # Rutas de las carpetas
    raw_dir = Path("data/raw")
    
    # Preguntar al usuario por opciones
    print("--- Configuración de Procesamiento ---")
    add_filename = input("¿Desea agregar una columna con el nombre del archivo original? (s/n): ").lower() == 's'
    apply_filter = input("¿Desea filtrar los datos por entidad? (s/n): ").lower() == 's'
    
    entidad = None
    if apply_filter:
        try:
            entidad = int(input("Ingrese el número de la entidad a filtrar (ej. 21): "))
            filtered_dir = Path("data/filtered")
            output_file = filtered_dir / f"datos_filtrados_entidad_{entidad}.csv"
            output_dir = filtered_dir
        except ValueError:
            print("Entrada no válida. Se usará la entidad 21 por defecto.")
            entidad = 21
            filtered_dir = Path("data/filtered")
            output_file = filtered_dir / "datos_filtrados_entidad_21.csv"
            output_dir = filtered_dir
    else:
        merged_dir = Path("data/merged")
        output_file = merged_dir / "datos_unificados.csv"
        output_dir = merged_dir

    # Crear la carpeta de salida si no existe
    output_dir.mkdir(parents=True, exist_ok=True)

    # Buscar todos los archivos .csv en data/raw
    csv_files = list(raw_dir.glob("*.csv"))

    if not csv_files:
        print("No se encontraron archivos CSV en data/raw.")
        return

    print(f"\nArchivos encontrados: {[f.name for f in csv_files]}")

    # Leer y concatenar todos los archivos
    dfs = []
    for f in csv_files:
        try:
            print(f"Procesando: {f.name}...")
            df = pd.read_csv(f, low_memory=False, encoding="latin-1")
            
            if apply_filter:
                # Filtrar por ENTIDAD_RES o ENTIDAD_NAC
                df = df[(df["ENTIDAD_RES"] == entidad) | (df["ENTIDAD_NAC"] == entidad)]
            
            # Reparar codificación de PAIS_NACIONALIDAD si existe
            if "PAIS_NACIONALIDAD" in df.columns:
                df["PAIS_NACIONALIDAD"] = (
                    df["PAIS_NACIONALIDAD"]
                    .astype(str)
                    .str.encode("latin1", errors="ignore")
                    .str.decode("utf-8", errors="ignore")
                )

            if add_filename:
                # Añadir una columna con el nombre del archivo original
                df['ARCHIVO_ORIGEN'] = f.name
            
            dfs.append(df)
        except Exception as e:
            print(f"Error al leer {f.name}: {e}")

    if dfs:
        # Unificar
        print("\nConcatenando archivos...")
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Guardar
        df_final.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\nÉxito: Archivo guardado en {output_file}")
        print(f"Total de filas: {len(df_final)}")
    else:
        print("No se pudo procesar ningún archivo o no hubo coincidencias con el filtro.")

if __name__ == "__main__":
    unificar_csvs()
