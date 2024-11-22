const socket = io();

let userId = prompt(`Please choose a username.`);
let currentGameId = null;
let hand = [];

document.addEventListener("DOMContentLoaded", () => {
    // ON FIRST CONNECTION

    socket.emit("join_lobby", { user_id: userId });

    socket.on("user_id_granted", (data) => {
        console.log("user_id_granted", data);
    });

    socket.on("user_id_denied", (data) => {
        console.log("user_id_denied", data);
        userId = prompt(`Username ${userId} taken, please choose a new username.`);
        socket.emit("join_lobby", { user_id: userId });
    });

    // IN LOBBY

    // Request to create game
    document.getElementById("create-game").addEventListener("click", () => {
        const gameId = document.getElementById("game-id-input").value;
        const deckName = document.getElementById("deck-select").value;
        socket.emit("create_game", { game_id: gameId, user_id: userId, deckName: deckName });
    });

    // Response to user or game lists changing
    socket.on("lobby_update", (data) => {
        console.log("lobby_update", data);
        // Update user list
        let userList = document.getElementById("user-list");
        userList.innerHTML = "";
        const e_my_li = document.createElement("li");
        e_my_li.textContent = `${userId}`;
        const myb = document.createElement("b");
        myb.appendChild(e_my_li);
        userList.appendChild(myb);
        data.users.forEach((user) => {
            if (user != userId) {
                const e_user_li = document.createElement("li");
                e_user_li.textContent = user;
                userList.appendChild(e_user_li);
            }
        });

        // Update game list
        let gameList = document.getElementById("game-list");
        gameList.innerHTML = "";
        data.games.forEach((game) => {
            const e_game_li = document.createElement("li");
            e_game_li.textContent = game;
            e_game_li.classList.add("gamelink");
            gameList.appendChild(e_game_li);
            e_game_li.addEventListener("click", e => {
                let gameId = document.getElementById("game-id-input").value;
                socket.emit("join_game", { game_id: game, user_id: userId });
            })
        });
    });

    // Request to join game
    document.getElementById("join-game").addEventListener("click", () => {
        let gameId = document.getElementById("game-id-input").value;
        socket.emit("join_game", { game_id: gameId, user_id: userId });
    });

    // Response to join game
    socket.on("game_joined", (data) => {
        console.log("game_joined", data);
        enterGame();
        currentGameId = data["game_id"];
        document.getElementById("game-id").textContent = currentGameId;
    });

    // IN GAME

    // Request to draw card
    document.getElementById("draw-card").addEventListener("click", () => {
        socket.emit("draw_card", { game_id: currentGameId, user_id: userId });
    });

    // Request to leave game
    document.getElementById("leave-game").addEventListener("click", () => {
        socket.emit("leave_game", { game_id: currentGameId, user_id: userId });
        currentGameId = null;
        hand = [];
        enterLobby();
    });

    // Response to drawing card
    socket.on("card_drawn", (data) => {
        console.log("card_drawn", data);
        hand.push(JSON.stringify(data.card));
        updateHand();
    });

    // Response to cycling card
    socket.on("card_recycled", (data) => {
        console.log("card_recycled", data);
        updateHand();
    });

    // Response to game state changing
    socket.on("game_update", (data) => {
        console.log("game_update", data);
        // Update game info
        let gameInfo = document.getElementById("game-info");
        gameInfo.innerHTML = `<p>Cards in deck: ${data["deck_size"]}</p>`;
        let playerList = document.getElementById("player-list");
        playerList.innerHTML = "";
        data.players.forEach((player) => {
            let li = document.createElement("li");
            li.textContent = `${player.user_id} - Cards in hand: ${player.hand_size}`;
            playerList.appendChild(li);
        });

        // Update revealed cards
        const revealedList = document.getElementById("revealed-cards");
        revealedList.innerHTML = "";
        // revealedList.innerHTML = "<h2>Revealed Cards:</h2>";
        for (const [playerId, cards] of Object.entries(data.revealed_cards)) {
            const e_player_li = document.createElement("li");
            revealedList.appendChild(e_player_li);
            
            const e_span = document.createElement("span");
            e_span.textContent = `Player ${playerId} revealed:`;
            e_player_li.appendChild(e_span);
            
            const e_ul = document.createElement("ul");
            e_ul.classList.add("card-list");
            e_player_li.appendChild(e_ul);
            
            for (const card of cards) {
                const e_card_li = document.createElement("li");
                e_ul.appendChild(e_card_li);
                e_card_li.appendChild(createCardElement(card));
            }
        }
    });

    // ON ERROR

    socket.on("error", (data) => {
        console.error(data);
        alert(data.message);
    });
});

function enterGame() {
    document.getElementById("game").style.display = "block";
    document.getElementById("lobby").style.display = "none";
    updateHand();
}

function enterLobby() {
    document.getElementById("game").style.display = "none";
    document.getElementById("lobby").style.display = "flex";
}

function createCardElement(card, in_hand = false) {
    const e_carddiv = document.createElement("div");
    e_carddiv.classList.add("card_div");

    const e_name = document.createElement("span");
    e_name.classList.add("card_name")
    e_name.textContent = card.Name;
    e_carddiv.appendChild(e_name);

    const e_image = document.createElement("img");
    e_image.classList.add("card_image")
    e_image.src = card.Path;
    e_carddiv.appendChild(e_image);

    const e_description = document.createElement("span");
    e_description.classList.add("card_description")
    e_description.textContent = card.Description;
    e_description.title = card.Description;
    e_carddiv.appendChild(e_description);

    if (in_hand) {
        const e_handcard_div = document.createElement("div");
        e_handcard_div.classList.add("hand-card")
        e_handcard_div.appendChild(e_carddiv)

        const e_actions = document.createElement("div");
        e_actions.classList.add("card-actions");
        e_handcard_div.appendChild(e_actions);

        const e_recycle = document.createElement("button");
        e_recycle.classList.add("card-action");
        e_recycle.textContent = "Recycle";
        // Request to recycle card
        e_recycle.addEventListener("click", e => {
            console.log("click", "recycle", {card, hand, e})
            socket.emit("recycle_card", { game_id: currentGameId, user_id: userId, card: card });
            hand = hand.filter((c) => c != JSON.stringify(card));
            updateHand();
        })
        e_actions.appendChild(e_recycle);

        const e_reveal = document.createElement("button");
        e_reveal.classList.add("card-action");
        e_reveal.textContent = "Reveal";
        // Request to reveal card
        e_reveal.addEventListener("click", e => {
            console.log("click", "reveal", {card, hand, e})
            socket.emit("reveal_card", { game_id: currentGameId, user_id: userId, card: card });
            hand = hand.filter((c) => c != JSON.stringify(card));
            updateHand();
        })
        e_actions.appendChild(e_reveal);
        return e_handcard_div;
    } else {
        return e_carddiv;
    }
}

function updateHand() {
    const handDiv = document.getElementById("hand");
    handDiv.innerHTML = "";
    hand.forEach((card_str) => {
        const card = JSON.parse(card_str);
        const li = document.createElement("li");
        li.appendChild(createCardElement(card, (in_hand = true)));
        handDiv.appendChild(li);
    });
}
