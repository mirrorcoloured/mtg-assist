import os
import json

from models import hash_text, ollama_chat, lcm


def make_messages(prompt):
    return [
        {
            "role": "system",
            "content": "You are an expressive fantasy concept artist. The user will give you some text as a prompt and you must describe some imagery to be associated with it.",
        },
        {
            "role": "user",
            "content": "Non-dominant Hand\nBe defeated by the player to your left",
        },
        {
            "role": "assistant",
            "content": "hand physically yanked out of their grasp\nethereal, long-fingered hand\nfrom the left\nface contorts, shock and defeat, slump backwards,\nsurrounded, dimly lit, smoke-filled room\ncandles flickering ominously in the background",
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]


deck_folder = "../decks"
for deck_file in os.listdir(deck_folder):
    deck_name = os.path.splitext(os.path.basename(deck_file))[0]
    with open(os.path.join(deck_folder, deck_file), "r") as f:
        deck_data = json.load(f)
    for card in deck_data:
        card_hash = hash_text(str(card))[:8]
        filename = f"{deck_name}-{card_hash}.png"
        image_prompt = ollama_chat(
            make_messages("\n".join(card.values())),
            timeout=60,
        )["content"]
        lcm(filename, image_prompt)
