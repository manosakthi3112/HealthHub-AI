const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");

function handleKey(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Display user message
    appendMessage("You", message, "user");

    // Send message to server
    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        // Display bot response
        appendMessage("Bot", data.response, "bot");
        userInput.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;  // Auto-scroll
    })
    .catch(error => {
        console.error("Error:", error);
        appendMessage("Bot", "Error connecting to server. Please try again.", "bot");
    });
}

function appendMessage(sender, text, className) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", className);
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(messageDiv);
}
