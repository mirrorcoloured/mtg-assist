import os
import json

from tqdm import tqdm

from artgen.models import hash_text, ollama_chat, lcm


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


def card_filename(deck_name: str, card: dict) -> str:
    card_hash = hash_text(str(card))[:8]
    return f"{deck_name}-{card_hash}.png"


def card_content(card: dict) -> str:
    return "\n".join(card.values())


def make_card_art(deck_name: str, card: dict):
    filename = card_filename(deck_name, card)
    if filename not in os.listdir(art_folder):
        image_prompt = ollama_chat(
            make_messages(card_content(card)),
            timeout=60,
        )["content"]
        lcm(os.path.join(art_folder, filename), image_prompt)


if __name__ == "__main__":
    print("Generating art for cards")
    deck_folder = "../decks"
    art_folder = "../art"

    for deck_file in os.listdir(deck_folder):
        deck_name = os.path.splitext(os.path.basename(deck_file))[0]
        with open(os.path.join(deck_folder, deck_file), "r") as f:
            deck_data = json.load(f)
        for card in tqdm(deck_data):
            make_card_art(deck_name, card)
