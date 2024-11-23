import os
import json

from tqdm import tqdm

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


def make_safe_filename(text):
    keepcharacters = (" ", ".", "_")
    return "".join(c for c in text if c.isalnum() or c in keepcharacters).strip()


def card_content(card: dict) -> str:
    return "\n".join(card.values())


def make_card_art(deck_name: str, card: dict, art_folder: str = "./art"):
    filename = make_safe_filename(card["Name"]) + ".png"
    if filename not in os.listdir(os.path.join(art_folder, deck_name)):
        image_prompt = ollama_chat(
            make_messages(card_content(card)),
            timeout=60,
        )["content"]
        lcm(os.path.join(art_folder, deck_name, filename), image_prompt)


if __name__ == "__main__":
    print("Generating art for cards")
    deck_folder = "./decks"
    art_folder = "./art"

    for deck_file in os.listdir(deck_folder):
        deck_name = os.path.splitext(os.path.basename(deck_file))[0]
        with open(os.path.join(deck_folder, deck_file), "r") as f:
            deck_data = json.load(f)
        for card in tqdm(deck_data):
            make_card_art(deck_name, card)
