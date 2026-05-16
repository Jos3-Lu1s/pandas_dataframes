import pandas as pd
from pathlib import Path

def mostrar_encabezados():
    raw_dir = Path("data/raw")
    csv_files = list(raw_dir.glob("*.csv"))

    if not csv_files:
        print("No se encontraron archivos CSV en data/raw.")
        return

    print("\n--- Inspección de Encabezados (Detectar errores de codificación) ---")
    for f in csv_files:
        print(f"\nArchivo: {f.name}")
        try:
            with open(f, 'rb') as binary_file:
                # Leer la primera línea como bytes
                first_line_raw = binary_file.readline()
                
                # Probar diferentes codificaciones comunes
                for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                    try:
                        decoded = first_line_raw.decode(enc)
                        # Mostrar solo los primeros 150 caracteres para no saturar
                        print(f"  [{enc:10}]: {decoded.strip()[:150]}...")
                    except UnicodeDecodeError:
                        print(f"  [{enc:10}]: [ERROR DE DECODIFICACIÓN]")
        except Exception as e:
            print(f"  Error al abrir el archivo: {e}")
    print("-" * 60)

def unificar_csvs():
    # Rutas de las carpetas
    raw_dir = Path("data/raw")
    
    # Preguntar al usuario por opciones
    print("\n--- Configuración de Procesamiento ---")
    inspect = input("¿Desea inspeccionar los encabezados antes de continuar? (s/n): ").lower() == 's'
    if inspect:
        mostrar_encabezados()

    add_filename = input("\n¿Desea agregar una columna con el nombre del archivo original? (s/n): ").lower() == 's'
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
            
            # Detección automática de codificación (UTF-8 con BOM vs Latin-1)
            encoding_to_use = "latin-1"
            with open(f, 'rb') as test_file:
                raw_bytes = test_file.read(3)
                if raw_bytes == b'\xef\xbb\xbf':
                    encoding_to_use = "utf-8-sig"
            
            print(f"  Codificación detectada: {encoding_to_use}")
            df = pd.read_csv(f, low_memory=False, encoding=encoding_to_use)
            
            # Limpiar nombres de columnas por si acaso hay espacios extra
            df.columns = [col.strip().replace('"', '') for col in df.columns]
            
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
        
        # Opción para quitar duplicados
        print("\n--- Limpieza de Duplicados ---")
        drop_dup = input("¿Desea eliminar registros duplicados? (s/n): ").lower() == 's'
        if drop_dup:
            print("\nColumnas disponibles:", list(df_final.columns))
            cols_input = input("Ingrese las columnas para identificar duplicados separadas por coma (o presione Enter para usar TODAS): ").strip()
            
            subset = None
            if cols_input:
                subset = [c.strip() for c in cols_input.split(',')]
                # Validar que las columnas existan
                subset = [c for c in subset if c in df_final.columns]
                if not subset:
                    print("No se reconocieron las columnas ingresadas. Se usarán todas.")
                    subset = None
            
            before_count = len(df_final)
            df_final = df_final.drop_duplicates(subset=subset)
            after_count = len(df_final)
            print(f"Registros eliminados: {before_count - after_count}")
            print(f"Registros restantes: {after_count}")

        # Opción para eliminar columnas
        print("\n--- Selección de Columnas ---")
        drop_cols = input("¿Desea eliminar algunas columnas? (s/n): ").lower() == 's'
        if drop_cols:
            print("\nColumnas actuales:", list(df_final.columns))
            cols_to_drop_input = input("Ingrese los nombres de las columnas a ELIMINAR separadas por coma: ").strip()
            
            if cols_to_drop_input:
                cols_to_drop = [c.strip() for c in cols_to_drop_input.split(',')]
                # Validar que las columnas existan antes de intentar borrarlas
                valid_cols_to_drop = [c for c in cols_to_drop if c in df_final.columns]
                
                if valid_cols_to_drop:
                    df_final = df_final.drop(columns=valid_cols_to_drop)
                    print(f"Columnas eliminadas: {valid_cols_to_drop}")
                else:
                    print("No se encontraron columnas válidas para eliminar.")

        # Guardar
        df_final.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\nÉxito: Archivo guardado en {output_file}")
        print(f"Total de filas: {len(df_final)}")
    else:
        print("No se pudo procesar ningún archivo o no hubo coincidencias con el filtro.")

if __name__ == "__main__":
    unificar_csvs()
