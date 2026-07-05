import os
from dotenv import load_dotenv
import yaml

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# CORS
# -------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Helpers
# -------------------------
def to_bool(value):
    return str(value).lower() in ["true", "1", "yes", "on"]

def coerce(key, value):
    if key in ["port", "workers"]:
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)

# -------------------------
# Endpoint
# -------------------------
@app.get("/")
@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    # Layer 1: defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # Layer 2: YAML
    with open("config.development.yaml") as f:
        yaml_cfg = yaml.safe_load(f)

    for k, v in yaml_cfg.items():
        config[k] = coerce(k, v)

    # Layer 3: .env
    load_dotenv(override=False)

    env_map = {
        "NUM_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
        "APP_PORT": "port",
    }

    for env_key, cfg_key in env_map.items():
        val = os.getenv(env_key)
        if val is not None:
            config[cfg_key] = coerce(cfg_key, val)

    # Layer 4: OS Environment (APP_*)
    os_map = {
        "APP_WORKERS": "workers",
        "APP_PORT": "port",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in os_map.items():
        if env_key in os.environ:
            config[cfg_key] = coerce(cfg_key, os.environ[env_key])

    # Layer 5: CLI overrides
    for item in set:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        if k in config:
            config[k] = coerce(k, v)

    # Mask secret
    config["api_key"] = "****"

    return config
