"""Reset only the explicitly isolated synthetic browser database, never the app database."""

import os

import psycopg
from psycopg import sql

from config.env import read_environment

config = read_environment(os.environ)
db = config["database"]
name = db["NAME"]
if config["mode"] != "test" or not name.endswith("_browser"):
    raise RuntimeError("Only a synthetic *_browser database in test mode can be reset")
with psycopg.connect(
    dbname="postgres",
    user=db["USER"],
    password=db["PASSWORD"],
    host=db["HOST"],
    port=db["PORT"],
    autocommit=True,
) as connection:
    connection.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid()",
        (name,),
    )
    connection.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))
    connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
print("Synthetic browser database prepared; application database untouched.")
