from config.bot import bot_config

TORTOISE_CONFIG = {
    "connections": {"default": bot_config.database_url},
    "apps": {
        "ravenbot": {
            "models": ["models", "aerich.models"],
            "default_connection": "default"
        }
    }
}
