import os
import json

from tqdm import tqdm

from models import ollama_chat, lcm


def make_messages(prompt):
    return [
        {
            "role": "system",
            # "content": "You are an expressive fantasy concept artist. The user will give you some text as a prompt and you must describe some imagery to be associated with it. Be creative an artistic by including non-obvious connections and ideas. Include style",
            "content": "\n".join(
                [
                    "Create just one sentence, various sentences each time. The sentence should be diverse and include subjects, characters or professions, styles, photo styles, a mix of art styles, lighting styles, expressions or feelings, moods, sentence structures, and compositions. Do not use “I, me, my, you, we, ours, or us” as the subject. Do not include an affirmative response in the results, just create the sentence we needed, only one sentence in each response. The sentence must be less than 50 words. ONLY respond with the image prompt. Examples:"
                ]
            ),
        },
        {
            "role": "user",
            "content": "Beast Slayer\nDefeat a beast in single combat.",
        },
        {
            "role": "assistant",
            "content": "A female warrior holding the head of an enormous white lion on her spear, detailed face and eyes, in the style of Peter Mohrbacher, dynamic lighting",
        },
        {
            "role": "user",
            "content": "Surf's Up!\nRide a wave successfully",
        },
        {
            "role": "assistant",
            "content": "a man surfing a wave in Bali, by Miyazaki, Nausicaa Ghibli, Breath of The Wild",
        },
        {
            "role": "user",
            "content": "Something's Up There\nDiscover a large flying artifact.",
        },
        {
            "role": "assistant",
            "content": "strange, old, spaceship, by Alexander Jansson, volumetric lighting, cinematic composition, high contrast, matte painting, highly detailed",
        },
        {
            "role": "user",
            "content": "To Rule Them All\nDefeat Sauron and obtain the One Ring",
        },
        {
            "role": "assistant",
            "content": "glamour shot of Sauron, morbide, dark, very detailed, rendered in octane, wet, dense atmospheric, epic, dramatic, empty, creepy, trail cam footage, photorealistic, hyperornate details, John Tolkien, photographed by Irakli Nadar and Reylia Slaby",
        },
        {
            "role": "user",
            "content": "Angelic Winter\nSummon an angel in the artic",
        },
        {
            "role": "assistant",
            "content": "A stunning portrait of a female valkyrie descending, aurora borealis in the background, centered, intricate, highly detailed, breathtaking beauty, precise lineart, vibrant, comprehensive cinematic, Bastien Lecouffe-Deharme, volumetric atmosphere, midnight",
        },
        # {
        #     "role": "user",
        #     "content": "Lynnemar\nMythical forest city of the fae, known for its charm and beauty.",
        # },
        # {
        #     "role": "assistant",
        #     # "content": "hand physically yanked out of their grasp\nethereal, long-fingered hand\nfrom the left\nface contorts, shock and defeat, slump backwards,\nsurrounded, dimly lit, smoke-filled room\ncandles flickering ominously in the background",
        #     "content": "Wide shot angle of fantasy forest city with interconnected vine walkways structures built into massive trees with tropical biome, redshift render medium angle shot of fantasy treehouse metropolis with magical buildings built into the flora with people sitting standing walking around the complex city, hyperrealistic, colorful, intricate detail, bold contrast lighting",
        # },
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


def make_card_prompt(deck_name: str, card: dict, art_folder: str = "./art"):
    filename = make_safe_filename(card["Name"]) + ".txt"
    if filename in os.listdir(os.path.join(art_folder, deck_name)):
        with open(
            os.path.join(art_folder, deck_name, filename), "r", encoding="utf-8"
        ) as f:
            return f.read()
    else:
        image_prompt = ollama_chat(
            make_messages(card_content(card)),
            timeout=60,
        )["content"]
        with open(
            os.path.join(art_folder, deck_name, filename), "w", encoding="utf-8"
        ) as f:
            f.write(image_prompt)
        return image_prompt


def make_card_art(deck_name: str, card: dict, art_folder: str = "./art"):
    filename = make_safe_filename(card["Name"]) + ".png"
    if filename not in os.listdir(os.path.join(art_folder, deck_name)):
        image_prompt = make_card_prompt(deck_name, card, art_folder)
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
