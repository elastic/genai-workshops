import { useEffect, useState, useRef } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
<img src="/elastic.svg" alt="Elastic Logo" className="elastic-logo" />


export default function App() {
  const [messages, setMessages] = useState(() => {
    const stored = localStorage.getItem("bookchat-history");
    return stored
      ? JSON.parse(stored)
      : [{ role: "system", text: "Hi friend! Ask me some questions about our fab book database!" }];
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    const trimmed = messages.slice(-20);
    localStorage.setItem("bookchat-history", JSON.stringify(trimmed));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/books-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          history: messages.map((m) => m.text),
        }),
      });

      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error getting response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-title">
        <img src="/elastic.svg" alt="Elastic" className="elastic-logo" />
        Elastic Book Chat</h2>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>
            <ReactMarkdown
              components={{
                p: ({ node, ...props }) => <p style={{ marginBottom: "1em" }} {...props} />,
                strong: ({ node, ...props }) => <strong style={{ fontWeight: 600 }} {...props} />,
                ul: ({ node, ...props }) => <ul style={{ paddingLeft: "1.2em", marginBottom: "1em" }} {...props} />,
                li: ({ node, ...props }) => <li style={{ marginBottom: "0.5em" }} {...props} />,
              }}
            >
              {msg.text}
            </ReactMarkdown>
            </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="input-row">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask me about books..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );


}
