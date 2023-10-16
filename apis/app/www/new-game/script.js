async function fetchUsers() {
    try {
        const response = await fetch('/api/v1/users');
        const users = await response.json();
        const userListElement = document.getElementById('user-list');
        users.forEach(user => {
            const listItem = document.createElement('li');
            listItem.textContent = user.username;
            listItem.addEventListener('click', async () => {
                try {
                    // Assuming the logged-in user is the white player and the clicked user is the black player
                    // Adjust accordingly if this assumption is not correct
                    const startGameResponse = await fetch(`/api/v1/games/start_game/${user.username}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                    });
                    const gameData = await startGameResponse.json();

                    if (gameData && gameData.id) {
                        window.location.href = `/app/game/#${gameData.id}`;
                    } else {
                        console.error('Unexpected game data:', gameData);
                    }
                } catch (error) {
                    console.error('Error starting game:', error);
                }
            });
            userListElement.appendChild(listItem);
        });
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

fetchUsers();