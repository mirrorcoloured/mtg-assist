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
        let gameId = document.getElementById("game-id").value;
        socket.emit("create_game", { game_id: gameId, user_id: userId });
    });

    // Response to user or game lists changing
    socket.on("lobby_update", (data) => {
        console.log("lobby_update", data);
        function createLiWith(text) {
            const li = document.createElement("li");
            li.textContent = text;
            return li;
        }
        // Update user list
        let userList = document.getElementById("user-list");
        userList.innerHTML = "";
        const myli = createLiWith(`${userId}`);
        const myb = document.createElement("b");
        myb.appendChild(myli);
        userList.appendChild(myb);
        data.users.forEach((user) => {
            if (user != userId) {
                userList.appendChild(createLiWith(user));
            }
        });

        // Update game list
        let gameList = document.getElementById("game-list");
        gameList.innerHTML = "";
        data.games.forEach((game) => {
            gameList.appendChild(createLiWith(game));
        });
    });

    // Request to join game
    document.getElementById("join-game").addEventListener("click", () => {
        let gameId = document.getElementById("game-id").value;
        socket.emit("join_game", { game_id: gameId, user_id: userId });
    });

    // Response to join game
    socket.on("game_joined", (data) => {
        console.log("game_joined", data);
        document.getElementById("lobby").style.display = "none";
        document.getElementById("game").style.display = "block";
        currentGameId = data["game_id"];
    });

    // IN GAME

    // Request to draw card
    document.getElementById("draw-card").addEventListener("click", () => {
        socket.emit("draw_card", { game_id: currentGameId, user_id: userId });
    });

    // Request to reveal card
    document.getElementById("hand").addEventListener("click", (event) => {
        console.log("CLICK", event.target.tagName, event.target.parentElement.tagName, event.target.textContent);
        if (event.target.tagName === "SPAN" && event.target.parentElement.tagName === "DIV") {
            if (event.target.textContent === "|Discard|") {
                let card = event.target.parentElement.getAttribute("x-card");
                socket.emit("discard_card", { game_id: currentGameId, user_id: userId, card: JSON.parse(card) });
                hand = hand.filter((c) => c != card);
                updateHand();
            } else if (event.target.textContent === "|Reveal|") {
                let card = event.target.parentElement.getAttribute("x-card");
                socket.emit("reveal_card", { game_id: currentGameId, user_id: userId, card: JSON.parse(card) });
                hand = hand.filter((c) => c != card);
                updateHand();
            }
        }
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

    // Response to discarding card
    socket.on("card_discarded", (data) => {
        console.log("card_discarded", data);
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
            const e_li = document.createElement("li");
            const e_span = document.createElement("span");
            // e_span.textContent = `Player ${playerId} revealed: ${cards.join(", ")}`;
            e_span.textContent = `Player ${playerId} revealed:`;
            e_li.appendChild(e_span);
            for (const card of cards) {
                e_li.appendChild(createCardElement(card));
            }
            revealedList.appendChild(e_li);
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
}

function enterLobby() {
    document.getElementById("game").style.display = "none";
    document.getElementById("lobby").style.display = "block";
}

function createCardElement(card, in_hand = false) {
    const e_div = document.createElement("div");
    e_div.setAttribute("x-card", JSON.stringify(card));
    e_div.classList.add("card");

    const e_title = document.createElement("span");
    e_title.textContent = card.ShortText;
    e_title.title = card.LongText;
    e_div.appendChild(e_title);

    if (in_hand) {
        const e_discard = document.createElement("span");
        e_discard.textContent = "|Discard|";
        e_discard.classList.add("clickable");
        e_div.appendChild(e_discard);

        const e_reveal = document.createElement("span");
        e_reveal.textContent = "|Reveal|";
        e_reveal.classList.add("clickable");
        e_div.appendChild(e_reveal);
    }

    return e_div;
}

function updateHand() {
    const handDiv = document.getElementById("hand");
    handDiv.innerHTML = "";
    const handList = document.createElement("ul");
    hand.forEach((card_str) => {
        const card = JSON.parse(card_str);
        const li = document.createElement("li");
        li.appendChild(createCardElement(card, (in_hand = true)));
        handList.appendChild(li);
    });
    handDiv.appendChild(handList);
}
