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
const askInput = document.getElementById('ask-input');
const answerBox = document.getElementById('ask-answer');
const answerText = document.getElementById('ask-answer-text');
const submitButton = askForm ? askForm.querySelector('button[type="submit"]') : null;
const micButton = document.getElementById('mic-button');
const speakButton = document.getElementById('speak-button');

let lastAnswer = '';

function speak(text) {
    if (!('speechSynthesis' in window) || !text) return;
    window.speechSynthesis.cancel(); // stop any answer already being read
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.02;
    window.speechSynthesis.speak(utterance);
}

if (askForm) {
    askForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const question = askInput.value.trim();
        const city = askForm.dataset.city;

        if (!question) return;

        submitButton.disabled = true;
        submitButton.textContent = 'Asking...';
        answerBox.hidden = false;
        answerBox.classList.remove('is-error');
        answerText.textContent = 'Thinking...';
        if (speakButton) speakButton.hidden = true;
        window.speechSynthesis && window.speechSynthesis.cancel();

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
                answerText.textContent = data.error || 'Something went wrong. Try again.';
                lastAnswer = '';
            } else {
                answerBox.classList.remove('is-error');
                answerText.textContent = data.answer;
                lastAnswer = data.answer;
                if (speakButton) {
                    speakButton.hidden = false;
                    speak(data.answer);
                }
            }
        } catch (err) {
            answerBox.classList.add('is-error');
            answerText.textContent = 'Could not reach the AI right now. Try again shortly.';
            lastAnswer = '';
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Ask';
        }
    });
}

if (speakButton) {
    speakButton.addEventListener('click', function () {
        speak(lastAnswer);
    });
}

// Voice input: only shown if the browser actually supports it (Chrome/Edge;
// Safari/Firefox support is inconsistent, so this is a progressive
// enhancement, never a requirement to use the Ask box).
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition && micButton) {
    micButton.hidden = false;

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    let listening = false;

    micButton.addEventListener('click', function () {
        if (listening) {
            recognition.stop();
            return;
        }
        recognition.start();
    });

    recognition.addEventListener('start', function () {
        listening = true;
        micButton.classList.add('is-listening');
    });

    recognition.addEventListener('end', function () {
        listening = false;
        micButton.classList.remove('is-listening');
    });

    recognition.addEventListener('result', function (e) {
        const transcript = e.results[0][0].transcript;
        askInput.value = transcript;
        askForm.requestSubmit();
    });

    recognition.addEventListener('error', function (e) {
        listening = false;
        micButton.classList.remove('is-listening');
        if (e.error === 'not-allowed') {
            answerBox.hidden = false;
            answerBox.classList.add('is-error');
            answerText.textContent = 'Microphone access was blocked. Check your browser permissions to use voice input.';
        }
    });
}