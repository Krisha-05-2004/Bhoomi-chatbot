// ===============================
// GLOBAL TTS STATE
// ===============================
let currentUtterance = null;
let speakingEl = null;


// ===============================
// CLEAN TEXT
// ===============================
function cleanForTTS(text) {
    if (!text) return "";
    return text
        .replace(/`+/g, "")
        .replace(/\*+/g, "")
        .replace(/\n+/g, ". ")
        .replace(/\s+/g, " ")
        .trim();
}


// ===============================
// SPEAK / STOP FUNCTION
// ===============================
function speakTextForEl(el) {
    if (!el) return;

    const text = cleanForTTS(
        el.querySelector('.msg-content')?.innerText || ''
    );

    if (!text.trim()) return;

    // If same message already speaking → STOP
    if (speechSynthesis.speaking && speakingEl === el) {
        speechSynthesis.cancel();
        speakingEl = null;
        return;
    }

    // Stop any previous speech
    speechSynthesis.cancel();

    currentUtterance = new SpeechSynthesisUtterance(text);

    const voices = speechSynthesis.getVoices();
    const voice =
        voices.find(v => v.lang === "en-IN") ||
        voices.find(v => v.lang.startsWith("en")) ||
        voices[0];

    if (voice) currentUtterance.voice = voice;

    currentUtterance.onend = function () {
        speakingEl = null;
    };

    speakingEl = el;
    speechSynthesis.speak(currentUtterance);
}


// ===============================
// SEND MESSAGE
// ===============================
async function sendMessage() {

    const inputField = document.getElementById("question");
    const message = inputField.value.trim();
    const chatBox = document.getElementById("chatbox");

    if (!message) return;

    // User message
    const userMessage = document.createElement("div");
    userMessage.className = "user";
    userMessage.innerHTML = `<div class="msg-content">${message}</div>`;
    chatBox.appendChild(userMessage);

    inputField.value = "";


    // Backend call
    const response = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            question: message,
            lang: document.getElementById("lang-select").value
        })
    });


const j = await response.json();

chatBox.scrollTop = chatBox.scrollHeight;



    // Bot message
    const botMessage = document.createElement("div");
    botMessage.className = "bot";

    const content = document.createElement("div");
    content.className = "msg-content";
    content.innerHTML = data.answer;
    botMessage.appendChild(content);


speakBtn.title = 'Speak';
speakBtn.addEventListener('click', () => speakTextForEl(el));
controls.appendChild(speakBtn);

    botMessage.appendChild(controls);
    chatBox.appendChild(botMessage);

    chatBox.scrollTop = chatBox.scrollHeight;
}


// ===============================
// EVENTS
// ===============================
document.addEventListener("DOMContentLoaded", function () {

    const sendBtn = document.getElementById("send-btn");
    const input = document.getElementById("question");

    if (sendBtn) sendBtn.addEventListener("click", sendMessage);

    if (input) {
        input.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
    }
});
