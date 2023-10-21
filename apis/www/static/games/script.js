async function fetchGames() {
    const response = await fetch('/api/v1/games');
    const games = await response.json();

    const gameListElement = document.getElementById('game-list');
    games.forEach(game => {
        const gameElement = document.createElement('li');

        const gameLink = document.createElement('a');
        gameLink.href = `/app/game/#${game.id}`;
        gameElement.appendChild(gameLink);

        const blackPlayerSpan = document.createElement('span');
        blackPlayerSpan.setAttribute('data-color', 'black');
        blackPlayerSpan.textContent = game.black_player_id;
        gameLink.appendChild(blackPlayerSpan);

        const vsIndicator = document.createElement('span');
        vsIndicator.textContent = 'vs';
        vsIndicator.className = 'vs-indicator';
        gameLink.appendChild(vsIndicator);

        const whitePlayerSpan = document.createElement('span');
        whitePlayerSpan.setAttribute('data-color', 'white');
        whitePlayerSpan.textContent = game.white_player_id;
        gameLink.appendChild(whitePlayerSpan);

        gameListElement.appendChild(gameElement);
    });
}
