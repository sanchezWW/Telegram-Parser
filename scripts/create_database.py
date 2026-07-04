"""Создаёт базу TelegramParser на локальном SQL Server Express."""

import pyodbc

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "TelegramParser"


def main() -> None:
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE=master;"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(
        f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'{DATABASE}') "
        f"CREATE DATABASE [{DATABASE}]"
    )
    conn.close()
    print(f"База данных '{DATABASE}' на {SERVER} готова.")


if __name__ == "__main__":
    main()
