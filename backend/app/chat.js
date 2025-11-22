// Enhanced NeuroCare AI Chat with fallback to chatbot
class ChatSession {
    constructor() {
        this.sessionId = Date.now();
        this.username = localStorage.getItem('currentUser') || 'User';
        this.currentMood = localStorage.getItem('currentMood') || 'Neutral';
        this.isLoading = false;
        this.useChatbot = false; // Track if we're using the fallback chatbot
        
        this.initializeElements();
        this.setupEventListeners();
        this.startChat();
    }

    initializeElements() {
        this.chatContainer = document.getElementById('chat-container');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.endChatBtn = document.getElementById('end-chat-btn');
        this.backBtn = document.getElementById('back-btn');
        this.welcomeMessage = document.getElementById('welcome-message');
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.endChatBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to end this chat session?')) {
                this.endChat();
            }
        });

        this.backBtn.addEventListener('click', () => {
            window.location.href = '/results';
        });
    }

    startChat() {
        console.log('Starting NeuroCare AI chat session...');
        
        if (this.welcomeMessage) {
            this.welcomeMessage.remove();
        }

        const greeting = this.getGreeting();
        this.addMessage('assistant', greeting);
        
        this.enableInput();
    }

    getGreeting() {
        const moodGreetings = {
            'Happy/Calm': "Hello! I'm NeuroCare AI. I can see you're feeling positive and balanced today - that's wonderful! What would you like to talk about?",
            'Neutral': "Hello! I'm NeuroCare AI. I see you're in a stable mood today. How has your day been so far?",
            'Stressed': "Hello! I'm NeuroCare AI. I notice you might be feeling some stress. I'm here to listen and help you work through whatever is on your mind.",
            'Depressed/Low': "Hello! I'm NeuroCare AI. I sense you might be going through a difficult time. Please know I'm here to support you without judgment.",
            'Tired/Exhausted': "Hello! I'm NeuroCare AI. It seems like you might be feeling drained today. Let's talk about what's been weighing on you."
        };

        return moodGreetings[this.currentMood] || "Hello! I'm NeuroCare AI, your mental wellness companion. I'm here to listen and support you. How are you feeling today?";
    }

    enableInput() {
        this.messageInput.disabled = false;
        this.sendBtn.disabled = false;
        this.messageInput.placeholder = "Type your message to NeuroCare AI...";
        this.messageInput.focus();
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        console.log('Sending message:', message);
        
        this.addMessage('user', message);
        this.messageInput.value = '';
        
        this.showTypingIndicator();
        this.setLoading(true);
        
        try {
            let response;
            
            if (!this.useChatbot) {
                // Try main chat system first
                try {
                    response = await this.tryMainChat(message);
                    console.log('✅ Main chat response received');
                } catch (mainError) {
                    console.log('🔄 Main chat failed, trying chatbot...');
                    this.useChatbot = true;
                    response = await this.tryChatbot(message);
                }
            } else {
                // Use chatbot directly
                response = await this.tryChatbot(message);
            }
            
            this.removeTypingIndicator();
            this.addMessage('assistant', response);
            
        } catch (error) {
            console.log('💥 All systems failed, using local AI');
            this.removeTypingIndicator();
            
            const localResponse = await this.getLocalResponse(message);
            this.addMessage('assistant', localResponse);
        } finally {
            this.setLoading(false);
        }
    }

    async tryMainChat(message) {
        const moodLogId = localStorage.getItem('currentMoodLogId');
        
        if (!moodLogId) {
            throw new Error('No mood log ID available');
        }

        const response = await fetch('/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: this.sessionId,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`Main chat HTTP ${response.status}`);
        }

        const data = await response.json();
        return data.response;
    }

    async tryChatbot(message) {
        const response = await fetch('/chatbot/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: this.username,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`Chatbot HTTP ${response.status}`);
        }

        const data = await response.json();
        return data.bot_reply;
    }

    async getLocalResponse(userMessage) {
        const message = userMessage.toLowerCase();
        
        // Enhanced local responses that match chatbot intents
        if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
            return "Hello! I'm NeuroCare AI. How can I support you today?";
        }
        
        if (message.includes('sad') || message.includes('depressed') || message.includes('down')) {
            return "I'm really sorry you're feeling this way. Want to share what's troubling you?";
        }
        
        if (message.includes('anxious') || message.includes('anxiety') || message.includes('worried')) {
            return "Anxiety can be overwhelming. Do you know what triggered it?";
        }
        
        if (message.includes('stress') || message.includes('stressed') || message.includes('overwhelmed')) {
            return "Stress can feel overwhelming. Let's break this down together.";
        }
        
        if (message.includes('sleep') || message.includes('tired') || message.includes('exhausted')) {
            return "Sleep issues can really affect your wellbeing. How's your sleep been lately?";
        }
        
        if (message.includes('bye') || message.includes('goodbye')) {
            return "Take care! I'm always here if you need me.";
        }
        
        // Default empathetic responses
        const defaultResponses = [
            "I understand... please tell me more about how you're feeling.",
            "Thank you for sharing that with me. Would you like to explore this further?",
            "I'm listening carefully. Could you tell me more about what's on your mind?",
            "That sounds important. How has this been affecting you?",
            "I appreciate you opening up about this. What would help you feel better?",
            "Let's work through this together. What do you think might help?"
        ];
        
        return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
    }

    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role === 'user' ? 'user-message' : 'ai-message'}`;
        messageDiv.textContent = content;
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.textContent = 'NeuroCare AI is thinking...';
        
        this.chatContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.messageInput.disabled = loading;
        this.sendBtn.disabled = loading;
        
        if (loading) {
            this.sendBtn.innerHTML = '<span>Thinking...</span>';
        } else {
            this.sendBtn.innerHTML = '<span>Send</span><span>➤</span>';
        }
    }

    endChat() {
        if (confirm('Are you sure you want to end this chat session?')) {
            window.location.href = '/results';
        }
    }
}

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Chat page loaded - starting NeuroCare AI with chatbot integration');
    new ChatSession();
});