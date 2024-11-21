import os
import json
import logging
import datetime

import httpx


# endpoint = "http://192.168.86.110:11434"
# endpoint = "https://chat.slcy.me"
endpoint = "http://localhost:11434"

response = httpx.get(
    f"{endpoint}/api/tags",
    headers={
        "accept": "application/json",
        "Content-Type": "application/json",
    },
    timeout=30,
)
[(m["name"], m["model"]) for m in response.json()["models"]]
