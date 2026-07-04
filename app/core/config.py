from urllib.parse import quote_plus

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    API_ID: int
    API_HASH: str
    DEBUG: bool = True

    # SQL Server — проще указывать отдельно, чем в одной длинной URL-строке
    MSSQL_SERVER: str = r"localhost\SQLEXPRESS"
    MSSQL_DATABASE: str = "TelegramParser"
    MSSQL_DRIVER: str = "ODBC Driver 17 for SQL Server"
    MSSQL_TRUSTED_CONNECTION: bool = True
    MSSQL_USERNAME: str | None = None
    MSSQL_PASSWORD: str | None = None

    class Config:
        env_file = ".env"

    def build_database_url(self) -> str:
        parts = [
            f"DRIVER={{{self.MSSQL_DRIVER}}}",
            f"SERVER={self.MSSQL_SERVER}",
            f"DATABASE={self.MSSQL_DATABASE}",
            "TrustServerCertificate=yes",
        ]

        if self.MSSQL_TRUSTED_CONNECTION:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.MSSQL_USERNAME}")
            parts.append(f"PWD={self.MSSQL_PASSWORD}")

        connection_string = ";".join(parts) + ";"
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"


settings = Settings()
