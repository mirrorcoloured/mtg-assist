import os
import json
import logging
import datetime
import random
import uuid
import urllib.request
import urllib.parse
import base64
import hashlib

import httpx
import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)


#####

# server_address = os.environ.get("IMGEN_ADDRESS")
server_address = "192.168.86.110:8188"
comfy_http_endpoint = f"http://{server_address}"
comfy_ws_endpoint = f"ws://{server_address}"
client_id = str(uuid.uuid4())


def connect_ws(ws):
    if ws.connected:
        return True
    try:
        ws.connect(f"{comfy_ws_endpoint}/ws?clientId={client_id}")
        # print("Connected to imgen")
        print("Connected to imgen")
        return True
    except TimeoutError:
        # print("No connection to imgen")
        print("No connection to imgen")
        # raise HTTPException(503, "No connection to imgen")
    except ConnectionRefusedError:
        # print("No connection to imgen")
        print("No connection to imgen")
        # raise HTTPException(503, "No connection to imgen")
    except OSError:
        # print("No connection to imgen")
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
        # data=json.dumps(
        #     {
        #         "prompt": prompt,
        #         "client_id": client_id,
        #     }
        # ).encode("utf-8"),
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
    filename: str,
    promptpos: str,
    promptneg: str = "poor quality, amateur, blurry, ugly, bad hand, abstract",
    seed: int = "0",
    sampler: str = "euler",
    scheduler: str = "normal",
    checkpoint: str = "'sd15\\realcartoon3d_v11.safetensors",
):
    with open("artgen/lcm.json", "r") as f:
        prompt = json.load(f)

    prompt["4"]["inputs"]["ckpt_name"] = checkpoint
    prompt["3"]["inputs"]["sampler_name"] = sampler
    prompt["3"]["inputs"]["scheduler"] = scheduler
    prompt["3"]["inputs"]["seed"] = seed
    prompt["6"]["inputs"]["text"] = promptpos
    prompt["7"]["inputs"]["text"] = promptneg

    outputs = get_images(prompt)
    output_bytes = outputs["20"][0]
    with open(os.path.join("artgen", "art", filename), "wb") as f:
        f.write(output_bytes)


llm_endpoint = "http://localhost:11434"


def ask_llm(prompt: str):
    response = httpx.post(
        # f"{llm_endpoint}/api/chat",
        # json={
        #     "model": "gemma2:2b",
        #     "messages": [
        #         {
        #             "role": "system",
        #             "content": "You are an expressive fantasy concept artist. The user will give you some text as a prompt and you must describe some imagery to be associated with it.",
        #         },
        #         {
        #             "role": "user",
        #             "content": "{'ShortText': 'Non-dominant Hand', 'LongText': 'Be defeated by the player to your left'}",
        #         },
        #         {
        #             "role": "assistant",
        #             "content": "hand physically yanked out of their grasp\nethereal, long-fingered hand\nfrom the left\nface contorts, shock and defeat, slump backwards,\nsurrounded, dimly lit, smoke-filled room\ncandles flickering ominously in the background",
        #         },
        #         {"role": "user", "content": prompt},
        #     ],
        #     "stream": False,
        # },
        f"{llm_endpoint}/api/generate",
        json={
            # "model": "gemma2:2b",
            "model": "moondream:latest",
            "prompt": """+ Instruction:
You are an expressive fantasy concept artist. The user will give you some text as a prompt and you must describe some imagery to be associated with it.

+ Prompt:
Non-dominant Hand
Be defeated by the player to your left

+ Description:
hand physically yanked out of their grasp\nethereal, long-fingered hand\nfrom the left\nface contorts, shock and defeat, slump backwards,\nsurrounded, dimly lit, smoke-filled room\ncandles flickering ominously in the background

+ Prompt:
{prompt}

+ Description:
""",
            "stream": False,
        },
        headers={
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    # return response.json()["message"]["content"]
    return response.json()["response"]


deck_folder = "./decks"
for deck_file in os.listdir(deck_folder):
    deck_name = os.path.splitext(os.path.basename(deck_file))[0]
    with open(os.path.join(deck_folder, deck_file), "r") as f:
        deck_data = json.load(f)
    for card in deck_data[3:]:
        card_hash = hash_text(str(card))[:8]
        filename = f"{deck_name}-{card_hash}.png"
        prompt = ask_llm("\n".join(card.values()))
        lcm(filename, prompt)
