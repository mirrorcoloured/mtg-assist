import random
import json

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, emit

from artgen.genart import card_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "abetting irritated diamonds"
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
)


# Data structures to store lobby and game information
class Game:
    def __init__(self, game_id, creator, deckname="objectives_v1"):
        self.game_id = game_id
        self.players = {}
        self.deck = self.create_deck(deckname)
        self.shuffle_deck()
        self.revealed_cards = {}
        self.add_player(creator)

    def create_deck(self, name):
        with open(f"./decks/{name}.json", "r") as f:
            cards = json.load(f)
            for card in cards:
                card["Path"] = "art/" + card_filename(name, card)
            return cards

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def draw_card(self, player_id):
        if self.deck and len(self.deck) > 0:
            card: dict = self.deck.pop(0)
            self.players[player_id]["hand"].append(card)
            return card
        else:
            return None

    def recycle_card(self, player_id, card):
        if card in self.players[player_id]["hand"]:
            self.players[player_id]["hand"].remove(card)
            self.deck.append(card)

    def add_player(self, player_id):
        self.players[player_id] = {"hand": [], "revealed": []}

    def remove_player(self, player_id):
        if player_id in self.players:
            # Return player's cards to the deck
            self.deck.extend(self.players[player_id]["hand"])
            del self.players[player_id]

    def get_state(self):
        return {
            "players": [
                {
                    "user_id": pid,
                    "hand_size": len(info["hand"]),
                    "revealed": info.get("revealed", []),
                }
                for pid, info in self.players.items()
            ],
            "deck_size": len(self.deck),
            "revealed_cards": self.revealed_cards,
        }


# In-memory storage
sid_userid = {}
userid_sid = {}
games: dict[str, Game] = {}
lobby_users = set()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/art/<path:path>")
def send_report(path):
    return send_from_directory("./art/", path)


@app.route("/art")
def get_art():
    print("requested art")
    # /artgen/art/objectives_v1-e4b48918.png
    return "ok"


@socketio.on("connect")
def handle_connect(data):
    print("connect", data, request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    print("disconnect", request.sid)
    sid = request.sid
    if sid in sid_userid:
        user_id = sid_userid[sid]

        # remove player from games
        empty_games = []
        for game_id, game in games.items():
            game.remove_player(user_id)
            socketio.emit(
                "game_update",
                games[game_id].get_state(),
                room=game_id,
            )
            if not games[game_id].players:
                empty_games.append(game_id)

        # remove empty games
        # for game_id in empty_games:
        #     del games[game_id]

        # remove player from tracking
        del sid_userid[sid]
        del userid_sid[user_id]
        lobby_users.discard(sid)

        send_lobby_update()


@socketio.on("debug")
def handle_debug(data):
    print("debug", sid_userid[request.sid], data)


@socketio.on("join_lobby")
def handle_join_lobby(data):
    print("join_lobby", request.sid, data)
    sid = request.sid
    requested_user_id = data["user_id"]
    if requested_user_id not in userid_sid:
        # register user
        userid_sid[requested_user_id] = sid
        sid_userid[sid] = requested_user_id

        # join lobby
        join_room("lobby", sid)
        lobby_users.add(sid)
        send_lobby_update()

        emit("user_id_granted", {"user_id": requested_user_id})
    else:
        emit("user_id_denied", {"user_id": requested_user_id})


@socketio.on("create_game")
def handle_create_game(data):
    print("create_game", sid_userid[request.sid], data)
    sid = request.sid
    user_id = sid_userid[sid]
    game_id = data["game_id"]
    if game_id not in games and game_id not in ["lobby"]:
        games[game_id] = Game(game_id, user_id)
        emit("game_created", {"game_id": game_id})
        send_lobby_update()
    else:
        emit("error", {"message": f"Game ID {game_id} already exists."})


@socketio.on("join_game")
def handle_join_game(data):
    print("join_game", sid_userid[request.sid], data)
    sid = request.sid
    user_id = sid_userid[sid]
    game_id = data["game_id"]
    if game_id in games:

        # join game
        join_room(game_id, sid)
        games[game_id].add_player(user_id)
        emit("game_joined", {"game_id": game_id})
        send_game_update(game_id)

        # leave lobby
        leave_room("lobby", sid)
        lobby_users.discard(sid)
        send_lobby_update()
    else:
        emit("error", {"message": "Game does not exist"})


@socketio.on("leave_game")
def handle_leave_game(data):
    print("leave_game", sid_userid[request.sid], data)
    sid = request.sid
    user_id = sid_userid[sid]
    game_id = data["game_id"]
    if game_id in games and user_id in games[game_id].players:
        # leave game
        leave_room(game_id, sid)
        games[game_id].remove_player(user_id)
        send_game_update(game_id)

        # join lobby
        join_room("lobby", sid)
        lobby_users.add(sid)
        send_lobby_update()

        # Clean up if no players left
        if not games[game_id].players:
            del games[game_id]
            send_lobby_update()
    else:
        emit("error", {"message": "Invalid game or user"})


@socketio.on("draw_card")
def handle_draw_card(data):
    print("draw_card", sid_userid[request.sid], data)
    sid = request.sid
    user_id = sid_userid[sid]
    game_id = data["game_id"]
    if game_id in games and user_id in games[game_id].players:
        card = games[game_id].draw_card(user_id)
        if card:
            emit("card_drawn", {"card": card})
            send_game_update(game_id)
        else:
            emit("no_cards_left")
    else:
        emit("error", {"message": "Invalid game or user"})


@socketio.on("recycle_card")
def handle_recycle_card(data):
    print("recycle_card", sid_userid[request.sid], data)
    sid = request.sid
    user_id = sid_userid[sid]
    game_id = data["game_id"]
    card = data["card"]
    if game_id in games and user_id in games[game_id].players:
        games[game_id].recycle_card(user_id, card)
        emit("card_recycled", {"card": card})
        send_game_update(game_id)
    else:
        emit("error", {"message": "Invalid game or user"})


@socketio.on("reveal_card")
def handle_show_card(data):
    print("reveal_card", sid_userid[request.sid], data)
    sid = request.sid
    user_id = sid_userid[sid]
    game_id = data["game_id"]
    card = data["card"]
    if game_id in games and user_id in games[game_id].players:
        player_hand = games[game_id].players[user_id]["hand"]
        if card in player_hand:
            player_hand.remove(card)
            games[game_id].revealed_cards[user_id] = games[game_id].revealed_cards.get(
                user_id, []
            ) + [card]
            send_game_update(game_id)
        else:
            emit("error", {"message": "Card not in hand"})
    else:
        emit("error", {"message": "Invalid game or user"})


def send_lobby_update():
    socketio.emit(
        "lobby_update",
        {
            "users": [sid_userid[sid] for sid in lobby_users],
            "games": list(games.keys()),
        },
        to="lobby",
    )
    print("sent lobby update", "sid_userid", sid_userid, "userid_sid", userid_sid)


def send_game_update(game_id):
    socketio.emit(
        "game_update",
        games[game_id].get_state(),
        room=game_id,
    )


def get_game_state(game_id):
    game = games[game_id]
    return {
        "players": [
            {
                "user_id": pid,
                "hand_size": len(info["hand"]),
                "revealed": info.get("revealed", []),
            }
            for pid, info in game.players.items()
        ],
        "deck_size": len(game.deck),
        "revealed_cards": game.revealed_cards,
    }


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True)
