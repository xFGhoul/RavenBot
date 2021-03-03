from config.loader.configloader import config

TORTOISE_CONFIG = {
    "connections": {"default": config['DATABASE_URI']},
    "apps": {
        "ravenbot": {
            "models": ["models", "aerich.models"],
            "default_connection": "default"
        }
    }
}
