# KDD - Extracción de Conocimiento en Base de Datos (COVID-19 Puebla)

Este proyecto está diseñado para la extracción, transformación y carga (ETL) de datos relacionados con el COVID-19, con un enfoque específico en el estado de **Puebla, México** (Entidad 21).

## Estructura del Proyecto

```text
KDD/
├── data/
│   ├── docs/catalogos/    # Diccionarios y catálogos de datos en JSON.
│   ├── filtered/          # Archivos CSV procesados y filtrados.
│   └── raw/               # Archivos CSV originales (fuente de datos).
├── imports/               # Carpeta vinculada al contenedor de MongoDB para importación.
├── compose.yml            # Configuración de Docker para MongoDB.
├── main.py                # Script principal de procesamiento de datos.
└── requirements.txt       # Dependencias de Python.
```

## Requisitos

- **Python 3.x**
- **Docker y Docker Compose**

## Configuración e Instalación

1.  **Entorno de Python:**
    Se recomienda usar un entorno virtual:

    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # En Windows
    pip install -r requirements.txt
    ```

2.  **Infraestructura (MongoDB):**
    Levantar el contenedor de base de datos:
    ```bash
    docker-compose up -d
    ```

## Flujo de Trabajo

### 1. Preparación de Datos

Coloque los archivos CSV originales en la carpeta `data/raw/`.

### 2. Procesamiento (ETL)

Ejecute el script `main.py` para filtrar los registros que pertenecen a Puebla (residencia o nacimiento) y unificarlos en un solo archivo:

```bash
python main.py
```

El resultado se guardará en `data/filtered/datos_filtrados.csv`.

### 3. Importación a MongoDB

Para importar los datos procesados a la base de datos:

1.  Copie el archivo generado `data/filtered/datos_filtrados.csv` a la carpeta `imports/`.
2.  Ejecute el comando de importación dentro del contenedor de MongoDB:
    ```bash
    docker exec -it mongo mongoimport --username admin --password password123 --authenticationDatabase admin --db KddCovid19 --collection KddPuebla --type csv --headerline --file /imports/datos_filtrados.csv
    ```

## Notas Adicionales

- **Control de Versiones:** Los archivos `.csv` y `.xlsx` están ignorados en `.gitignore` para evitar subir grandes volúmenes de datos al repositorio. Asegúrese de respaldar sus datos originales y procesados de forma independiente.
