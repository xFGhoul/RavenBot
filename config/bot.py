from pydantic import BaseSettings


class BotConfig(BaseSettings):
    bot_token: str
    database_url: str

    class Config:
        env_file = ".env"


bot_config = BotConfig()
