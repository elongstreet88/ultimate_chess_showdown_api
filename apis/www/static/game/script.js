const game = new Chess();
const $status = $('#status');
const $fen = $('#fen');
const $pgn = $('#pgn');
let gameId = null;
let gameData = null; // Global declaration
let currentUser = null; // Global declaration

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});

function startWebSocket(gameId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/game_live_updates/${gameId}`);

    ws.onmessage = event => {
        const receivedFen = event.data;
        if (game.fen() !== receivedFen) {
            game.load(receivedFen);
            board.position(receivedFen, false);
            updateStatus();

            // Check if it's the current user's turn
            const isCurrentUserWhite = gameData.white_player_id === currentUser;
            const isWhiteTurn = game.turn() === 'w';
            if ((isCurrentUserWhite && isWhiteTurn) || (!isCurrentUserWhite && !isWhiteTurn)) {
                // If it is, make the mobile phone buzz
                if ("vibrate" in navigator) {
                    navigator.vibrate(200); // vibrate for 200ms
                }
            }
        }
    };

    ws.onerror = error => console.error(`WebSocket Error: ${error}`);
    ws.onclose = () => {
        console.log('WebSocket closed. Attempting to reconnect...');
        setTimeout(() => startWebSocket(gameId), 1000);
    };
}

async function startGame() {
    const response = await fetch('/api/v1/games/start_game/test_w/test_b', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    const data = await response.json();
    gameId = data.id;
}

async function sendMove(move) {
    const action = {
        action_type: 'MOVE',
        move: move.san
    };

    const response = await fetch(`/api/v1/games/${gameId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action)
    });

    return response.ok ? await response.json() : null;
}

function onDragStart(source, piece) {
    // Assuming you've fetched the current user outside the function and stored it in a variable named "currentUser"
    if ((game.turn() === 'w' && piece.startsWith('b')) || 
        (game.turn() === 'b' && piece.startsWith('w')) ||
        (game.turn() === 'w' && gameData.black_player_id === currentUser) ||
        (game.turn() === 'b' && gameData.white_player_id === currentUser)) {
        return false;
    }

    const moves = game.moves({ square: source, verbose: true });
    $('#myBoard .square-55d63').css('background', '');

    // Clear existing blue dots first
    $('.blue-dot').remove();

    moves.forEach(move => {
        const squareEl = $('#myBoard .square-' + move.to);
        if (!squareEl.find('.blue-dot').length) {  // only append if there's no existing dot
            const dot = $('<div>').css({
                width: '10px',
                height: '10px',
                backgroundColor: 'blue',
                borderRadius: '50%',
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                opacity: 0  // initially set opacity to 0
            }).addClass('blue-dot');
            squareEl.append(dot);
            setTimeout(() => dot.css('opacity', 1), 0);  // fades the dot in
        }
    });
}


async function onDrop(source, target) {
    $('#myBoard .square-55d63').css('background', '');
    $('.blue-dot').remove();

    const move = game.move({ from: source, to: target, promotion: 'q' });
    if (!move) return 'snapback';

    const moveResponse = await sendMove(move);
    if (!moveResponse) {
        game.undo();
        return 'snapback';
    }

    updateStatus();
}

function updateStatus() {
    let status = '';
    const moveColor = game.turn() === 'b' ? 'Black' : 'White';

    if (game.in_checkmate()) {
        status = `Game over, ${moveColor} is in checkmate.`;
    } else if (game.in_draw()) {
        status = 'Game over, drawn position';
    } else {
        status = `${moveColor} to move`;
        if (game.in_check()) {
            status += `, ${moveColor} is in check`;
        }
    }

    $status.html(status);
    $fen.html(game.fen());
}

const config = {
    draggable: true,
    position: 'start',
    onDragStart,
    onDrop,
    onSnapEnd: () => board.position(game.fen()),
    moveSpeed: 1,
    snapbackSpeed: 1,
    snapSpeed: 1,
    appearspeed: 'fast',
    pieceTheme: 'https://raw.githubusercontent.com/oakmac/chessboardjs/master/website/img/chesspieces/alpha/{piece}.png',
};

const boardWidth = Math.min(window.innerWidth, window.innerHeight) - 10;
$('#myBoard').css('width', `${boardWidth}px`);

async function getGameData(gameId) {
    try {
        const response = await fetch(`/api/v1/games/${gameId}`);
        if (!response.ok) throw new Error('Failed to fetch game data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(error);
        return null;
    }
}

function setPlayerNames(whiteName, blackName) {
    const whitePlayerNameElement = document.getElementById('white-player-name');
    const blackPlayerNameElement = document.getElementById('black-player-name');

    whitePlayerNameElement.textContent = whiteName;
    blackPlayerNameElement.textContent = blackName;
}

async function getCurrentUser() {
    try {
        const response = await fetch('/api/v1/user');
        if (!response.ok) throw new Error('Failed to fetch user data');

        const data = await response.json();
        return data.username;
    } catch (error) {
        console.error(error);
        return null;
    }
}


(async function init() {
    gameId = location.hash.substr(1);
    let initialPosition = 'start';

    if (!gameId) {
        const response = await startGame();
        gameId = response.id;
        location.hash = `#${gameId}`;
        setPlayerNames(response.white_player_id, response.black_player_id); // Set player names
    } else {
        gameData = await getGameData(gameId);
        setPlayerNames(gameData.white_player_id, gameData.black_player_id); // Set player names
    }

    // Fetch the current user's username
    currentUser = await getCurrentUser();

    if (gameData.white_player_id === currentUser) {
        config.orientation = 'white';
    } else if (gameData.black_player_id === currentUser) {
        config.orientation = 'black';
    } else { // If the currentUser is neither the white nor black player, then they are viewing only.
        config.draggable = false; // Disable piece dragging.
    }

    game.load(gameData.fen);
    config.position = gameData.fen;
    board = Chessboard('myBoard', config);

    startWebSocket(gameId);
    updateStatus();
})();