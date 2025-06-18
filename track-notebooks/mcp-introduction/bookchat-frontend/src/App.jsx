import { useEffect, useState, useRef } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import elasticLogo from "/elastic.svg";

export default function App() {
  const [messages, setMessages] = useState(() => {
    const stored = localStorage.getItem("bookchat-history");
    return stored
      ? JSON.parse(stored)
      : [{ role: "assistant", text: "Hi friend! Ask me some questions about our fab book database!" }];
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    const trimmed = messages.slice(-20);
    localStorage.setItem("bookchat-history", JSON.stringify(trimmed));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleClearChat = () => {
    setMessages([
      {
        role: "assistant",
        text: "Hi friend! Ask me some questions about our fab book database!",
      },
    ]);
    setInput("");
    setLoading(false);
  };

  const sendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", text: input };
    const newMessages = [...messages, userMessage]; // Store this to use it in catch block
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const frontendOrigin = window.location.origin;
      const backendBaseUrl = frontendOrigin.replace('-3000-', '-8000-');
      const apiUrl = `${backendBaseUrl}/api/books-chat`;

      console.log("Contacting backend at:", apiUrl);

      const res = await fetch(apiUrl, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          history: messages.map((m) => m.text).filter(Boolean),
        }),
      });

      if (!res.ok) {
        throw new Error(`Server responded with status: ${res.status}`);
      }

      const data = await res.json();
      // Use newMessages here to avoid including a potential error message in the next history
      setMessages([...newMessages, { role: "assistant", text: data.response }]);
    } catch (error) {
      console.error("Error getting response:", error);
      setMessages([
        ...newMessages,
        { role: "assistant", text: "Sorry, an error occurred while getting the response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-title">
        <img src={elasticLogo} alt="Elastic" className="elastic-logo" />
        Elastic Book Chat
      </h2>

      <div className="messages">
        {messages.map((msg, i) => (
          msg.role !== 'system' && (
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
          )
        ))}

        {loading && (
          <div className="message assistant">
            <strong>Assistant:</strong>
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="input-row" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Ask me about books..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>

      <div className="clear-button-container">
        <button onClick={handleClearChat} className="clear-button">
          Clear Chat
        </button>
      </div>
    </div>
  );
}
