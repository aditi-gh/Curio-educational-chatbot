document.addEventListener('DOMContentLoaded', function() {
    // Chat functionality
    if (document.getElementById('chat-box')) {
        const chatBox = document.getElementById('chat-box');
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        
        // Scroll to bottom of chat
        function scrollToBottom() {
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        // Add message to chat
        function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
            
            const now = new Date();
            const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            messageDiv.innerHTML = `
                <div class="message-content">${content}</div>
                <div class="message-time">${timeString}</div>
            `;
            
            chatBox.appendChild(messageDiv);
            scrollToBottom();
        }
        
        // Handle sending messages
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (message === '') return;
            
            addMessage(message, true);
            chatInput.value = '';
            
            try {
                const response = await fetch('/get_response', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ user_input: message })
                });
                
                const data = await response.json();
                addMessage(data.response, false);
            } catch (error) {
                addMessage("Sorry, I'm having trouble connecting. Please try again later.", false);
            }
        }
        
        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Initial greeting
        setTimeout(() => {
            addMessage("Hello! I'm your educational assistant. Ask me anything about math, science, history, or literature.", false);
        }, 500);
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = '#f87171';
                    setTimeout(() => {
                        input.style.borderColor = '#e9ecef';
                    }, 2000);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});