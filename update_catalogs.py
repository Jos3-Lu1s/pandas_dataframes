import json
from pathlib import Path
from pymongo import MongoClient
import sys

def apply_catalogs():
    # Configuración de MongoDB
    # Estos valores se obtuvieron de compose.yml y README.md
    uri = "mongodb://admin:password123@localhost:27017/?authSource=admin"
    db_name = "KddCovid19"
    collection_name = "KddPuebla"
    
    catalogs_dir = Path("data/docs/catalogos")
    
    if not catalogs_dir.exists():
        print(f"Error: La carpeta {catalogs_dir} no existe.")
        return

    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Verificar si la colección tiene documentos
        count = collection.count_documents({})
        if count == 0:
            print(f"Advertencia: La colección {collection_name} está vacía. ¿Ya importaste los datos?")
            # Podríamos continuar, pero es mejor avisar.
        
        print(f"Iniciando actualización de catálogos en {db_name}.{collection_name}...")

        json_files = sorted(list(catalogs_dir.glob("*.json")))
        
        for json_file in json_files:
            print(f"Procesando {json_file.name}...", end=" ", flush=True)
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    pipeline = json.load(f)
                
                # Ejecutar el pipeline de actualización
                # El formato de los archivos JSON es una lista de etapas (usualmente un solo $set)
                # que MongoDB puede usar como un pipeline de actualización.
                result = collection.update_many({}, pipeline)
                print(f"Hecho. (Modificados: {result.modified_count})")
            except Exception as e:
                print(f"Error: {e}")

        print("\n¡Proceso de actualización completado!")

    except Exception as e:
        print(f"Error de conexión a MongoDB: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    apply_catalogs()
