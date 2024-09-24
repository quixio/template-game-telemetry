class WebSocketClient {
    constructor(url, session_id, cheater_callback) {
        this.url = url;
        this.session_id = session_id;
        this.cheater_callback = cheater_callback;
        this.connect();
    }

    connect() {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
        };

        this.socket.onmessage = (event) => {
            this.handleMessage(event.data);
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket connection closed', event);
            // Optionally, you can try to reconnect after a delay
            setTimeout(() => this.connect(), 1000);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error', error);
        };
    }

    stripLeadingBAndQuotes(str) {
        if (str.startsWith("b'") && str.endsWith("'")) {
            return str.slice(2, -1);
        }
        return str;
    }

    handleMessage(message) {
        console.log('Received message:', message);
        const data = JSON.parse(message);
        const session_id = this.stripLeadingBAndQuotes(data.session_id);
        if (session_id === this.session_id && data.is_bot == 1) {
            if(this.cheater_callback) this.cheater_callback();
        }
    }

    displayMessage(data) {
        const messagesDiv = document.getElementById('messages');
        const messageElement = document.createElement('div');
        messageElement.textContent = `ID: ${data.id}, is_bot: ${data.is_bot}`;
        if (data.is_bot) {
            messageElement.classList.add('highlight');
        }
        messagesDiv.appendChild(messageElement);
    }
}

// Export the class for use in other files
export default WebSocketClient;