def build_context(chat_history, max_history):
    history = chat_history[-max_history:]
    return "\n".join(
        f"User: {h['user']}\nBhoomi: {h['bot']}"
        for h in history
    )
