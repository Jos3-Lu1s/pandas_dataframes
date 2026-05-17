import pandas as pd
from pathlib import Path
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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

        # Opción para convertir fechas
        print("\n--- Conversión de Fechas ---")
        convert_dates = input("¿Desea convertir las columnas de fecha a formato temporal? (s/n): ").lower() == 's'
        if convert_dates:
            date_cols = [c for c in df_final.columns if 'FECHA' in c.upper()]
            if date_cols:
                print(f"Columnas detectadas para conversión: {date_cols}")
                for col in date_cols:
                    # Forzamos formato YYYY-MM-DD para evitar advertencias y asegurar consistencia
                    df_final[col] = pd.to_datetime(df_final[col], format='%Y-%m-%d', errors='coerce')
                print("Conversión completada. Los valores como '9999-99-99' ahora son nulos.")
            else:
                print("No se encontraron columnas de fecha.")

        # Guardar en CSV
        df_final.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\nÉxito: Archivo CSV guardado en {output_file}")
        print(f"Total de filas: {len(df_final)}")

        # Opción para importar a MongoDB
        print("\n--- Importación a MongoDB ---")
        import_mongo = input("¿Desea importar los datos directamente a MongoDB? (s/n): ").lower() == 's'
        if import_mongo:
            try:
                uri = os.getenv("MONGO_URI", "mongodb://admin:password123@localhost:27017/?authSource=admin")
                db_name = os.getenv("MONGO_DB", "KddCovid19")
                collection_name = os.getenv("MONGO_COLLECTION", "KddPuebla")
                
                print(f"Conectando a MongoDB ({db_name}.{collection_name})...")
                client = MongoClient(uri)
                db = client[db_name]
                collection = db[collection_name]
                
                # Limpiar la colección antes de importar (opcional, podrías comentar esto)
                if input("¿Desea vaciar la colección antes de la importación? (s/n): ").lower() == 's':
                    collection.delete_many({})
                    print("Colección vaciada.")

                # Preparar datos: Pandas NaT/NaN deben ser None para MongoDB
                # Convertimos a object para que permita None en lugar de NaT
                print("Preparando datos para MongoDB (esto puede tomar un momento)...")
                df_temp = df_final.astype(object).where(pd.notnull(df_final), None)
                records = df_temp.to_dict('records')
                
                print(f"Insertando {len(records)} registros...")
                # Insertar en bloques para mayor seguridad con datasets grandes
                batch_size = 50000
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    collection.insert_many(batch)
                    print(f"  Progreso: {min(i + batch_size, len(records))}/{len(records)}")
                
                print("¡Importación a MongoDB completada con éxito!")
                client.close()
            except Exception as e:
                print(f"Error al importar a MongoDB: {e}")
    else:
        print("No se pudo procesar ningún archivo o no hubo coincidencias con el filtro.")

if __name__ == "__main__":
    unificar_csvs()
