import os
import tempfile
import time

import duckdb

dbFile = os.getenv('DBFILE', None)
if dbFile is None:
    print("Error, Please provide a database file.")
    exit(1)
file = os.getenv('FILE', None)
if file is None:
    print("Error, Please provide a file.")
    exit(1)
if not os.path.exists(file):
    print("Error, File does not exist.")
    exit(1)

dbFile = os.environ['GPTSCRIPT_WORKSPACE_DIR'] + '/' + dbFile

max_retries = 10
attempts = 0
success = False

while not success and attempts < max_retries:
    try:
        cursor = duckdb.connect(database=dbFile, config={'temp_directory': tempfile.gettempdir()})
        success = True
    except:
        time.sleep(1)
        attempts += 1

if success:
    file = os.path.basename(file)
    _, file_extension = os.path.splitext(file)
    table_name = os.path.basename(dbFile)
    table_name, _ = os.path.splitext(table_name)

    if file_extension == '.csv':
        load_query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv('{file}', escape = '\', header = true);"
    elif file_extension == '.xlsx':
        cursor.install_extension("spatial")
        cursor.load_extension("spatial")
        load_query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM st_read('{file}', open_options=['HEADERS=FORCE']);"
    elif file_extension == '.jsonl' or file_extension == '.ndjson' or file_extension == '.json':
        load_query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_json_auto('{file}');"
    else:
        print("Error, Unsupported file type. Please provide a .json, .ndjson, .jsonl, .csv, or .xlsx file.")
        exit(1)

    cursor.execute(load_query)

    try:
        schema_query = f"PRAGMA table_info('{table_name}');"
        print(f"Schema for table '{table_name}':")
        print(cursor.sql(schema_query).show(max_rows=10000000, max_width=10000000))
    except Exception as e:
        print(f"Failed to read schema: {e}")
        exit(1)
else:
    print("Failed to connect to database")
    exit(1)
