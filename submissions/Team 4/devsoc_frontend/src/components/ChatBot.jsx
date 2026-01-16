import { useState } from "react";
import Message from "./Message";

export default function ChatBox({ messages, onAsk, loading }) {
  const [input, setInput] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim()) return;
    onAsk(input);
    setInput("");
  }

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <Message key={idx} message={msg} />
        ))}
        {loading && (
          <div className="message assistant">
            Thinking…
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="input-box">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about MetaKGP..."
        />
        <button type="submit">Ask</button>
      </form>
    </div>
  );
}
