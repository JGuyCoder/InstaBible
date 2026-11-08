document.addEventListener("DOMContentLoaded", () => {
    const panel = document.getElementById("bobble-panel");
    const toggle = document.getElementById("bobble-toggle");
    const close = document.getElementById("bobble-close");
    const reset = document.getElementById("bobble-reset");
    const form = document.getElementById("bobble-form");
    const input = document.getElementById("bobble-input");
    const messages = document.getElementById("bobble-messages");

    // Open and close the chat panel
    toggle.addEventListener("click", () => {
        panel.hidden = !panel.hidden;
        toggle.setAttribute("aria-expanded", String(!panel.hidden));

        if (!panel.hidden) {
            input.focus();
        }
    });

    close.addEventListener("click", () => {
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
    });

    // Reset the conversation display
    reset.addEventListener("click", () => {
        messages.innerHTML = "";

        addMessage(
            "assistant",
            "Hey! I'm Bobble. What would you like to explore?"
        );
    });

    // Display a message in the chat
    function addMessage(role, text) {
        const message = document.createElement("div");

        message.classList.add("bobble-message", role);
        message.textContent = text;

        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }

    // Temporary response until the backend is connected
    form.addEventListener("submit", (event) => {
        event.preventDefault();

        const userMessage = input.value.trim();

        if (!userMessage) return;

        addMessage("user", userMessage);
        input.value = "";

        addMessage(
            "assistant",
            "I'm here! My connection to the Bobble backend isn't set up yet."
        );

        input.focus();
    });
});