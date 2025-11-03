// --- Voice Recording (STT) setup in input area ---
let recognition = null, isRecording = false;

window.addEventListener('DOMContentLoaded', function() {
  const voiceBtn = document.getElementById('voice-btn');
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    recognition = new (
      window.SpeechRecognition || window.webkitSpeechRecognition
    )();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    voiceBtn.addEventListener("click", function() {
      if (!isRecording) {
        recognition.start();
        isRecording = true;
        voiceBtn.textContent = "🎧 Recording...";
      }
    });

    recognition.onresult = function(event) {
      const transcript = event.results[0][0].transcript;
      document.getElementById("question").value = transcript;
      stopRecording();
      askBhoomi();
    };
    recognition.onerror = stopRecording;
    recognition.onend = stopRecording;
  } else {
    voiceBtn.disabled = true;
  }
});

function stopRecording() {
  isRecording = false;
  document.getElementById("voice-btn").textContent = "🎙️ Start";
}

// --- Main chat functions ---
function askBhoomi() {
  const input = document.getElementById("question");
  const chatBox = document.getElementById("chatbox");
  const query = input.value.trim();
  const lang = document.getElementById("lang-select").value;
// ...inside fetch body
 body: JSON.stringify({ question: message, lang: lang }) // for sendMessage
  if (!query) return;

  // Add user message
  const userDiv = document.createElement("div");
  userDiv.className = "user";
  userDiv.innerHTML = `<div class="text"><b>You:</b> ${query}</div>
    <span class="icon" onclick="editMessage(this)">✏️</span>
    <span class="icon" onclick="copyMessage(this)">📋</span>`;
  chatBox.appendChild(userDiv);
  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  const thinkingId = addThinkingMessage(chatBox);

  fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: query })
  })
    .then(res => res.json())
    .then(data => {
      removeThinkingMessage(thinkingId);
      const botDiv = document.createElement("div");
      botDiv.className = "bot";
      botDiv.innerHTML = `
        <div class="text"><b>Bhoomi:</b> ${data.answer || "Sorry, something went wrong."}</div>
        <span class="icon" onclick="copyMessage(this)">📋</span>
        <span class="icon" onclick="playVoice(this)">🔊</span>
        <span class="icon" onclick="stopVoice(this)">⏹️</span>
        <span class="icon" onclick="pauseVoice(this)">⏸️</span>
        <span class="icon" onclick="resumeVoice(this)">▶️</span>
      `;
      chatBox.appendChild(botDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
      speakText(data.answer);
    })
    .catch(err => {
      removeThinkingMessage(thinkingId);
      const botDiv = document.createElement("div");
      botDiv.className = "bot";
      botDiv.innerHTML = `<div class="text"><b>Bhoomi:</b> Error occurred.</div>`;
      chatBox.appendChild(botDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
    });
}

function addThinkingMessage(chatBox) {
  const thinkingMsg = document.createElement("div");
  thinkingMsg.className = "thinking";
  thinkingMsg.innerHTML = "Bhoomi is thinking...";
  const id = "thinking-" + Date.now();
  thinkingMsg.id = id;
  chatBox.appendChild(thinkingMsg);
  chatBox.scrollTop = chatBox.scrollHeight;
  return id;
}

function removeThinkingMessage(id) {
  const msg = document.getElementById(id);
  if (msg) msg.remove();
}

function speakText(text) {
  if ("speechSynthesis" in window) {
    if (speechSynthesis.speaking || speechSynthesis.pending)
      speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;
    speechSynthesis.speak(utterance);
  }
}

function playVoice(el) {
  stopVoice();
  const text = el.closest("div.bot").querySelector(".text").innerText;
  speakText(text);
}

function stopVoice(el) {
  if ("speechSynthesis" in window && (speechSynthesis.speaking || speechSynthesis.pending)) {
    speechSynthesis.cancel();
  }
}

function pauseVoice(el) {
  if ("speechSynthesis" in window && speechSynthesis.speaking) {
    speechSynthesis.pause();
  }
}

function resumeVoice(el) {
  if ("speechSynthesis" in window && speechSynthesis.paused) {
    speechSynthesis.resume();
  }
}

// --- Inline edit, copy, and ask-edited (user message) ---
function editMessage(el) {
  const msgDiv = el.closest(".user");
  const textDiv = msgDiv.querySelector(".text");
  const currentText = textDiv.innerText.replace("You:", "").trim();
  const inputEdit = document.createElement("input");
  inputEdit.type = "text";
  inputEdit.className = "inline-edit";
  inputEdit.value = currentText;
  msgDiv.replaceChild(inputEdit, textDiv);
  inputEdit.focus();

  function saveEdit() {
    const newText = inputEdit.value.trim();
    if (newText) {
      const textElement = document.createElement("div");
      textElement.className = "text";
      textElement.innerHTML = `<b>You:</b> ${newText}`;
      msgDiv.replaceChild(textElement, inputEdit);
      askEditedMessage(newText, msgDiv);
    } else {
      msgDiv.remove();
    }
  }
  inputEdit.addEventListener("blur", saveEdit);
  inputEdit.addEventListener("keydown", function(e) {
    if (e.key === "Enter") saveEdit();
  });
}

function askEditedMessage(newText, msgDiv) {
  const chatBox = document.getElementById("chatbox");
  let next = msgDiv.nextElementSibling;
  if (next && next.classList.contains("bot")) next.remove();
  const botDiv = document.createElement("div");
  botDiv.className = "bot";
  botDiv.innerHTML = `<div class="text"><b>Bhoomi:</b> ...thinking...</div>
                      <span class="icon" onclick="copyMessage(this)">📋</span>
                      <span class="icon" onclick="playVoice(this)">🔊</span>
                      <span class="icon" onclick="stopVoice(this)">⏹️</span>
                      <span class="icon" onclick="pauseVoice(this)">⏸️</span>
                      <span class="icon" onclick="resumeVoice(this)">▶️</span>`;
  msgDiv.after(botDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: newText })
  })
    .then(res => res.json())
    .then(data => {
      botDiv.querySelector(".text").innerHTML = `<b>Bhoomi:</b> ${data.answer || "Sorry, something went wrong."}`;
      speakText(data.answer);
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => {
      botDiv.querySelector(".text").innerHTML = `<b:Bhoomi:</b> Error occurred.`;
    });
}

function copyMessage(el) {
  const text = el.closest("div").querySelector(".text").innerText;
  navigator.clipboard.writeText(text).then(() => alert("Copied!"));
}

// Enter-to-send shortcut
document.getElementById("question").addEventListener("keypress", function(e) {
  if (e.key === "Enter") askBhoomi();
});
document.getElementById("uploadForm").addEventListener("submit", function(e){
  e.preventDefault();
  const fileInput = document.getElementById("imageUpload");
  if(fileInput.files.length === 0) return;
  const formData = new FormData();
  formData.append("image", fileInput.files[0]);

  fetch("/upload", {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => addMessage("bot", data.answer || "Sorry, could not analyze image."));
});
