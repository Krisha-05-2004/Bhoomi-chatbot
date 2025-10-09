async function askBhoomi() {
  const queryInput = document.getElementById("query");
  const chatBox = document.getElementById("chat-box");
  const query = queryInput.value.trim();
  
  if (!query) return;

  // Add user message
  chatBox.innerHTML += `<div class="user"><b>You:</b> ${query}</div>`;
  queryInput.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await response.json();

    if (data.answer) {
      chatBox.innerHTML += `<div class="bhoomi"><b>Bhoomi:</b> ${data.answer}</div>`;
    } else {
      chatBox.innerHTML += `<div class="bhoomi"><b>Bhoomi:</b> Sorry, something went wrong.</div>`;
    }

  } catch (error) {
    console.error("Error:", error);
    chatBox.innerHTML += `<div class="bhoomi"><b>Bhoomi:</b> I faced an error, please try again later.</div>`;
  }

  chatBox.scrollTop = chatBox.scrollHeight;
}
