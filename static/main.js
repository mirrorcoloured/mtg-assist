const socket = io();

let userId = 'user_' + Math.floor(Math.random() * 1000);
let currentGameId = null;
let hand = [];

document.addEventListener('DOMContentLoaded', () => {
    // Join lobby
    socket.emit('join_lobby', { user_id: userId });

    socket.on('error', data => {
        alert(data.message);
    });

    // Handle lobby updates
    socket.on('lobby_update', data => {
        updateLobby(data);
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

    // Show card
    document.getElementById('hand').addEventListener('click', event => {
        if (event.target.tagName === 'LI') {
            let card = event.target.textContent;
            socket.emit('show_card', { game_id: currentGameId, user_id: userId, card: parseInt(card) });
            // Remove card from hand
            hand = hand.filter(c => c != card);
            updateHand();
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
    // Update user list
    let userList = document.getElementById('user-list');
    userList.innerHTML = '';
    data.users.forEach(user => {
        let li = document.createElement('li');
        li.textContent = user;
        userList.appendChild(li);
    });

    // Update game list
    let gameList = document.getElementById('game-list');
    gameList.innerHTML = '';
    data.games.forEach(game => {
        let li = document.createElement('li');
        li.textContent = game;
        gameList.appendChild(li);
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
    let handDiv = document.getElementById('hand');
    handDiv.innerHTML = '<h2>Your Hand (Click a card to reveal):</h2>';
    let handList = document.createElement('ul');
    hand.forEach(card => {
        let li = document.createElement('li');
        li.textContent = card;
        handList.appendChild(li);
    });
    handDiv.appendChild(handList);
}