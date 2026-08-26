// Small ambient touch: a live clock in the header, styled like a station timestamp.
function updateClock() {
    const el = document.getElementById('header-clock');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
updateClock();
setInterval(updateClock, 1000);

// Ask AI: submits the question via fetch (no full page reload), grounded
// server-side in a fresh weather fetch for whichever city is on screen.
function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

const askForm = document.getElementById('ask-form');
if (askForm) {
    askForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const input = document.getElementById('ask-input');
        const answerBox = document.getElementById('ask-answer');
        const button = askForm.querySelector('button');
        const question = input.value.trim();
        const city = askForm.dataset.city;

        if (!question) return;

        button.disabled = true;
        button.textContent = 'Asking...';
        answerBox.hidden = false;
        answerBox.classList.remove('is-error');
        answerBox.innerHTML = '<span class="ai-summary-tag">AI</span>Thinking...';

        try {
            const response = await fetch(askForm.dataset.askUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ question, city }),
            });
            const data = await response.json();

            if (!response.ok) {
                answerBox.classList.add('is-error');
                answerBox.textContent = data.error || 'Something went wrong. Try again.';
            } else {
                answerBox.classList.remove('is-error');
                answerBox.innerHTML = '<span class="ai-summary-tag">AI</span>' + data.answer;
            }
        } catch (err) {
            answerBox.classList.add('is-error');
            answerBox.textContent = 'Could not reach the AI right now. Try again shortly.';
        } finally {
            button.disabled = false;
            button.textContent = 'Ask';
        }
    });
}
