from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")

    host: str
    port: int
    user: str
    password: SecretStr = Field(validation_alias="DB_PASS")
    name: str

    @property
    def url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
        )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")

    host: str
    port: int
    db: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class DeribitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DERIBIT_", env_file=".env", extra="ignore")

    url: str = "https://www.deribit.com/api/v2"
    timeout: float = 10
