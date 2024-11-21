const socket = io();

// let userId = 'user_' + Math.floor(Math.random() * 1000);
let userId = 'user_301';
let currentGameId = null;
let hand = [];

document.addEventListener('DOMContentLoaded', () => {
    // Join lobby

    userId = prompt(`Please choose a username.`)
    socket.emit('join_lobby', { user_id: userId });

    socket.on('user_id_granted', data => {
        console.log('GRANTED');
    });

    socket.on('user_id_denied', data => {
        console.log('DENIED');
        userId = prompt(`Username ${userId} taken, please choose a new username.`);
        socket.emit('join_lobby', { user_id: userId });
    });

    socket.on('error', data => {
        alert(data.message);
    });

    // Handle lobby updates
    socket.on('lobby_update', data => {
        updateLobby(data);
    });

    window.addEventListener("beforeunload", function (e) {
        socket.emit('leave_lobby', { user_id: userId });
    });

    // Create game
    document.getElementById('create-game').addEventListener('click', () => {
        let gameId = document.getElementById('game-id').value;
        currentGameId = gameId;
        socket.emit('create_game', { game_id: gameId, user_id: userId });
    });

    // Join game
    document.getElementById('join-game').addEventListener('click', () => {
        let gameId = document.getElementById('game-id').value;
        currentGameId = gameId;
        socket.emit('join_game', { game_id: gameId, user_id: userId });
    });

    // Handle game updates
    socket.on('game_update', data => {
        updateGame(data);
    });

    // Draw card
    document.getElementById('draw-card').addEventListener('click', () => {
        socket.emit('draw_card', { game_id: currentGameId, user_id: userId });
    });

    // Handle card drawn
    socket.on('card_drawn', data => {
        hand.push(data.card);
        updateHand();
    });

    // Handle card discarded
    socket.on('card_discarded', data => {
        updateHand();
    });

    // Show card
    document.getElementById('hand').addEventListener('click', event => {
        if (event.target.tagName === 'SPAN' && event.target.parentElement.tagName === 'LI') {
            if (event.target.textContent === "|Discard|") {
                let card = event.target.parentElement.getAttribute('x-card');
                socket.emit('discard_card', { game_id: currentGameId, user_id: userId, card: parseInt(card) });
                hand = hand.filter(c => c != card);
                updateHand();
            } else if (event.target.textContent === "|Reveal|") {
                let card = event.target.parentElement.getAttribute('x-card');
                socket.emit('show_card', { game_id: currentGameId, user_id: userId, card: parseInt(card) });
                hand = hand.filter(c => c != card);
                updateHand();
            }
        }
    });

    // Leave game
    document.getElementById('leave-game').addEventListener('click', () => {
        socket.emit('leave_game', { game_id: currentGameId, user_id: userId });
        currentGameId = null;
        hand = [];
        document.getElementById('game').style.display = 'none';
        document.getElementById('lobby').style.display = 'block';
    });
});

function updateLobby(data) {

    function createLiWith(text) {
        const li = document.createElement('li');
        li.textContent = text;
        return li
    }
    // Update user list
    let userList = document.getElementById('user-list');
    userList.innerHTML = '';
    const myli = createLiWith(`${userId}`);
    const myb = document.createElement('b');
    myb.appendChild(myli)
    userList.appendChild(myb);
    data.users.forEach(user => {
        if (user != userId) {
            userList.appendChild(createLiWith(user));
        }
    });

    // Update game list
    let gameList = document.getElementById('game-list');
    gameList.innerHTML = '';
    data.games.forEach(game => {
        gameList.appendChild(createLiWith(game));
    });
}

function updateGame(data) {
    // Switch to game view
    document.getElementById('lobby').style.display = 'none';
    document.getElementById('game').style.display = 'block';

    // Update game info
    let gameInfo = document.getElementById('game-info');
    gameInfo.innerHTML = `<p>Cards in deck: ${data['deck_size']}</p><h2>Players:</h2>`;
    let playerList = document.createElement('ul');
    data.players.forEach(player => {
        let li = document.createElement('li');
        li.textContent = `${player.user_id} - Cards in hand: ${player.hand_size}`;
        playerList.appendChild(li);
    });
    gameInfo.appendChild(playerList);

    // Update revealed cards
    let revealedDiv = document.getElementById('revealed-cards');
    revealedDiv.innerHTML = '<h2>Revealed Cards:</h2>';
    for (let [playerId, cards] of Object.entries(data.revealed_cards)) {
        let p = document.createElement('p');
        p.textContent = `Player ${playerId} revealed: ${cards.join(', ')}`;
        revealedDiv.appendChild(p);
    }
}

function updateHand() {
    const handDiv = document.getElementById('hand');
    handDiv.innerHTML = '<h2>Your Hand</h2>';
    const handList = document.createElement('ul');
    hand.forEach(card => {
        const li = document.createElement('li');
        const e_title = document.createElement('span');
        const e_discard = document.createElement('span');
        const e_reveal = document.createElement('span');
        li.setAttribute('x-card', card);
        e_title.textContent = card;
        e_discard.textContent = "|Discard|";
        e_reveal.textContent = "|Reveal|";
        li.appendChild(e_title);
        li.appendChild(e_discard);
        li.appendChild(e_reveal);
        handList.appendChild(li);
    });
    handDiv.appendChild(handList);
}