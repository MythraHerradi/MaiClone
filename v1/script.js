const sidebar = document.querySelector('#sidebar');
const messages = document.querySelector('#messages');
const form = document.querySelector('#chat-form');
const input = document.querySelector('#input');
const send = document.querySelector('#send');
const modelSelect = document.querySelector('#model');
const temperature = document.querySelector('#temperature');
const tempValue = document.querySelector('#temp-value');
const statusText = document.querySelector('#status');
const statusDot = document.querySelector('.dot');

const history = [];

temperature.addEventListener('input', () => { tempValue.textContent = Number(temperature.value).toFixed(1); });
document.querySelector('#toggle').addEventListener('click', () => sidebar.classList.toggle('open'));
document.querySelector('#clear').addEventListener('click', () => {
    history.length = 0;
    messages.innerHTML = '';
    addMessage('ai', 'Nouvelle conversation. Je t’écoute !');
});

input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
});
input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
    }
});

function setStatus(text, state = '') {
    statusText.textContent = text;
    statusDot.className = `dot ${state}`;
}

function addMessage(role, text, extraClass = '') {
    const wrapper = document.createElement('div');
    wrapper.className = `msg ${role} ${extraClass}`.trim();
    if (role === 'ai') {
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = 'M';
        wrapper.append(avatar);
    }
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    if (text) bubble.textContent = text;
    wrapper.append(bubble);
    messages.append(wrapper);
    messages.scrollTop = messages.scrollHeight;
    return { wrapper, bubble };
}

function showTyping() {
    const message = addMessage('ai', '');
    message.bubble.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
    return message.wrapper;
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage('user', text);
    history.push({ role: 'user', content: text });
    input.value = '';
    input.style.height = 'auto';
    send.disabled = true;
    setStatus('MaiClone écrit…', 'busy');
    const typing = showTyping();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: history.slice(0, -1),
                model: modelSelect.value,
                temperature: Number(temperature.value),
            }),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.error || result.detail || `HTTP ${response.status}`);
        const reply = result.reply ?? result.response ?? result.message ?? result.output ?? 'Aucune réponse.';
        typing.remove();
        addMessage('ai', reply);
        history.push({ role: 'assistant', content: reply });
        setStatus('prêt');
    } catch (error) {
        typing.remove();
        addMessage('ai', `Impossible d’obtenir une réponse.\n${error.message}`, 'error');
        setStatus('erreur', 'err');
    } finally {
        send.disabled = false;
        input.focus();
    }
});
