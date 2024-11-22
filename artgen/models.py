import os
import json
import uuid
import urllib.request
import urllib.parse
import hashlib
from pathlib import Path

import dotenv
import httpx
import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)


#####

comfy_server_address = "192.168.86.110:8188"
comfy_http_endpoint = f"http://{comfy_server_address}"
comfy_ws_endpoint = f"ws://{comfy_server_address}"
client_id = str(uuid.uuid4())

llm_endpoint = "https://chat.slcy.me"

print(f"{dotenv.load_dotenv()=}")
openwebui_host = os.environ["openwebui_host"]
openwebui_key = os.environ["openwebui_key"]
ollama_host = f"{openwebui_host}/ollama"
openwebui_key = os.environ["openwebui_key"]
ollama_headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openwebui_key}",
}

#####


def connect_ws(ws):
    if ws.connected:
        return True
    try:
        ws.connect(f"{comfy_ws_endpoint}/ws?clientId={client_id}")
        print("Connected to imgen")
        return True
    except TimeoutError:
        print("No connection to imgen")
    except ConnectionRefusedError:
        print("No connection to imgen")
    except OSError:
        print("No connection to imgen")


ws = websocket.WebSocket()
connect_ws(ws)

#####


def queue_prompt(prompt: dict) -> dict:
    response = httpx.post(
        f"{comfy_http_endpoint}/prompt",
        json={
            "prompt": prompt,
            "client_id": client_id,
        },
    )
    return response.json()


def get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{comfy_http_endpoint}/view?{url_values}") as response:
        return response.read()


def get_history(prompt_id: str) -> dict:
    response = httpx.get(f"{comfy_http_endpoint}/history/{prompt_id}")
    return response.json()


def get_images(prompt: dict) -> dict:
    connect_ws(ws)

    prompt_id = queue_prompt(prompt)["prompt_id"]
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break  # Execution is done
        else:
            continue  # previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for o in history["outputs"]:
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            if "images" in node_output:
                images_output = []
                for image in node_output["images"]:
                    image_data = get_image(
                        image["filename"], image["subfolder"], image["type"]
                    )
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images


def hash_text(prompt):
    return hashlib.sha1(
        json.dumps(prompt, sort_keys=True).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def lcm(
    filepath: Path,
    promptpos: str,
    promptneg: str = "poor quality, amateur, blurry, ugly, bad hand, abstract",
    seed: int = "0",
    cfg: int = "1.5",
    steps: int = "7",
    scheduler: str = "sgm_uniform",
    checkpoint: str = "sd15\\realcartoon3d_v11.safetensors",
    overwrite: bool = False,
):
    with open("lcm.json", "r") as f:
        prompt = json.load(f)

    prompt["4"]["inputs"]["ckpt_name"] = checkpoint
    prompt["3"]["inputs"]["scheduler"] = scheduler
    prompt["3"]["inputs"]["steps"] = steps
    prompt["3"]["inputs"]["cfg"] = cfg
    prompt["3"]["inputs"]["seed"] = seed
    prompt["6"]["inputs"]["text"] = promptpos
    prompt["7"]["inputs"]["text"] = promptneg

    outputs = get_images(prompt)
    output_bytes = outputs["20"][0]
    if os.path.isfile(filepath) and not overwrite:
        print(f"File already exists: {filepath}")
    else:
        with open(filepath, "wb") as f:
            f.write(output_bytes)


def ollama_chat(
    messages: list[dict[str, str]],
    model: str = "llama3.1:8b",
    timeout: int = 10,
) -> dict[str, str]:
    if type(messages) is str:
        messages = [{"role": "user", "content": messages}]
    response = httpx.post(
        f"{ollama_host}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
        },
        headers=ollama_headers,
        timeout=timeout,
    )
    if response.is_success:
        return response.json()["message"]
    else:
        print(response.content)
        raise Exception("Server error ↑")
