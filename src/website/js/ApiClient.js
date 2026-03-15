class ApiClient {
    constructor(endpoints) {
        this.endpoints = endpoints;
    }

    async get(url) {
        const response = await fetch(url);
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    }

    async post(url, body = null) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: body !== null ? JSON.stringify(body) : null,
        });
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    }

    async delete(url) {
        const response = await fetch(url, { method: "DELETE" });
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    }

    requestComputerTurn(payload) {
        return this.post(this.endpoints.MAKE_MOVE, payload);
    }

    requestNextBotMove(payload) {
        return this.post(this.endpoints.NEXT_MOVE, payload);
    }

    listGames(inProgressOnly = true) {
        return this.get(this.endpoints.LIST_GAMES(inProgressOnly));
    }

    loadGame(gameId) {
        return this.get(this.endpoints.LOAD_GAME(gameId));
    }

    listBotGames(inProgressOnly = false) {
        return this.get(this.endpoints.LIST_BOT_GAMES(inProgressOnly));
    }

    listBots() {
        return this.get(this.endpoints.LIST_BOTS);
    }

    loadBotGame(gameId) {
        return this.get(this.endpoints.LOAD_BOT_GAME(gameId));
    }

    renameGame(gameId, name) {
        return this.post(this.endpoints.UPDATE_GAME_NAME(gameId), { name });
    }

    restoreToMove(gameId, moveNumber) {
        return this.post(this.endpoints.RESTORE_TO_MOVE(gameId, moveNumber));
    }

    restoreBotToMove(gameId, moveNumber) {
        return this.post(this.endpoints.RESTORE_BOT_TO_MOVE(gameId, moveNumber));
    }

    listSnapshots(gameId) {
        return this.get(this.endpoints.LIST_SNAPSHOTS(gameId));
    }

    createSnapshot(gameId, label) {
        return this.post(this.endpoints.CREATE_SNAPSHOT(gameId), { label });
    }

    restoreSnapshot(gameId, snapshotId) {
        return this.post(this.endpoints.RESTORE_SNAPSHOT(gameId, snapshotId));
    }

    deleteGame(gameId) {
        return this.delete(this.endpoints.DELETE_GAME(gameId));
    }

    deleteBotGame(gameId) {
        return this.delete(this.endpoints.DELETE_BOT_GAME(gameId));
    }
}
