from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./musicapp.db"

    musicbrainz_app_name: str = "MusicApp"
    musicbrainz_app_version: str = "0.1.0"
    musicbrainz_contact: str = "dev@example.com"

    @property
    def musicbrainz_user_agent(self) -> str:
        return (
            f"{self.musicbrainz_app_name}/{self.musicbrainz_app_version} "
            f"({self.musicbrainz_contact})"
        )


settings = Settings()
