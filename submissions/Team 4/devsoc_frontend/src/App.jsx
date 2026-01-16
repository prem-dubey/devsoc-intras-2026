import { useState } from "react";
import axios from "axios";
import ChatBox from "./components/ChatBot";
import "./index.css";

const API_URL = "http://localhost:8000/query";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
async function handleAsk(question) {
  setMessages((prev) => [
    ...prev,
    { role: "user", text: question },
  ]);

  setLoading(true);

  try {
    const res = await axios.post(API_URL, {
      question: question,   // 👈 JSON body
    });

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text: res.data.answer,
        sources: res.data.sources || [],
      },
    ]);
  } catch (err) {
    console.error(err);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text: "Error contacting backend.",
        sources: [],
      },
    ]);
  } finally {
    setLoading(false);
  }
}


  return (
    <div className="app">
      <header className="header">
        <h1>GraphMind</h1>
        <p>Verified MetaKGP Question Answering</p>
      </header>

      <ChatBox
        messages={messages}
        onAsk={handleAsk}
        loading={loading}
      />
    </div>
  );
}
