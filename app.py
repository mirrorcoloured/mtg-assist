from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "abetting irritated diamonds"
socketio = SocketIO(app, cors_allowed_origins="*")


# Data structures to store lobby and game information
class Game:
    def __init__(self, game_id, creator):
        self.game_id = game_id
        self.players = {}
        self.deck = self.create_deck()
        self.shuffle_deck()
        self.revealed_cards = {}
        self.add_player(creator)

    def create_deck(self):
        # Simple deck of cards (e.g., numbers 1-52)
        return list(range(1, 53))

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def draw_card(self, player_id):
        if self.deck and len(self.deck) > 0:
            card = self.deck.pop(0)
            self.players[player_id]["hand"].append(card)
            return card
        else:
            return None

    def discard_card(self, player_id, card):
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


# In-memory storage
lobby_users = set()
games = {}


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("join_lobby")
def handle_join_lobby(data):
    user_id = data["user_id"]
    lobby_users.add(user_id)
    emit(
        "lobby_update",
        {"users": list(lobby_users), "games": list(games.keys())},
        broadcast=True,
    )


@socketio.on("leave_lobby")
def handle_leave_lobby(data):
    user_id = data["user_id"]
    lobby_users.discard(user_id)
    emit(
        "lobby_update",
        {"users": list(lobby_users), "games": list(games.keys())},
        broadcast=True,
    )


@socketio.on("create_game")
def handle_create_game(data):
    game_id = data["game_id"]
    user_id = data["user_id"]
    if game_id not in games:
        games[game_id] = Game(game_id, user_id)
        join_room(game_id)
        emit("game_created", {"game_id": game_id}, room=request.sid)
        emit(
            "lobby_update",
            {"users": list(lobby_users), "games": list(games.keys())},
            broadcast=True,
        )


@socketio.on("join_game")
def handle_join_game(data):
    game_id = data["game_id"]
    user_id = data["user_id"]
    if game_id in games:
        games[game_id].add_player(user_id)
        join_room(game_id)
        emit("game_joined", {"game_id": game_id}, room=request.sid)
        emit("game_update", get_game_state(game_id), room=game_id)
    else:
        emit("error", {"message": "Game does not exist"}, room=request.sid)


@socketio.on("draw_card")
def handle_draw_card(data):
    game_id = data["game_id"]
    user_id = data["user_id"]
    if game_id in games and user_id in games[game_id].players:
        card = games[game_id].draw_card(user_id)
        if card:
            emit("card_drawn", {"card": card}, room=request.sid)
            emit("game_update", get_game_state(game_id), room=game_id)
        else:
            emit("no_cards_left", room=request.sid)
    else:
        emit("error", {"message": "Invalid game or user"}, room=request.sid)


@socketio.on("discard_card")
def handle_discard_card(data):
    game_id = data["game_id"]
    user_id = data["user_id"]
    card = data["card"]
    if game_id in games and user_id in games[game_id].players:
        games[game_id].discard_card(user_id, card)
        if card:
            emit("card_discarded", {"card": card}, room=request.sid)
            emit("game_update", get_game_state(game_id), room=game_id)
        else:
            emit("no_cards_left", room=request.sid)
    else:
        emit("error", {"message": "Invalid game or user"}, room=request.sid)


@socketio.on("show_card")
def handle_show_card(data):
    game_id = data["game_id"]
    user_id = data["user_id"]
    card = data["card"]
    if game_id in games and user_id in games[game_id].players:
        player_hand = games[game_id].players[user_id]["hand"]
        if card in player_hand:
            player_hand.remove(card)
            games[game_id].revealed_cards[user_id] = games[game_id].revealed_cards.get(
                user_id, []
            ) + [card]
            emit("game_update", get_game_state(game_id), room=game_id)
        else:
            emit("error", {"message": "Card not in hand"}, room=request.sid)
    else:
        emit("error", {"message": "Invalid game or user"}, room=request.sid)


@socketio.on("leave_game")
def handle_leave_game(data):
    game_id = data["game_id"]
    user_id = data["user_id"]
    if game_id in games and user_id in games[game_id].players:
        games[game_id].remove_player(user_id)
        leave_room(game_id)
        emit("game_update", get_game_state(game_id), room=game_id)
        # Clean up if no players left
        if not games[game_id].players:
            del games[game_id]
            emit(
                "lobby_update",
                {"users": list(lobby_users), "games": list(games.keys())},
                broadcast=True,
            )
    else:
        emit("error", {"message": "Invalid game or user"}, room=request.sid)


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
    socketio.run(app, debug=True)
