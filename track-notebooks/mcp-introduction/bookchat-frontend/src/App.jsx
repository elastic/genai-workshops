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

    const handleClearChat = () => {
    // Reset the messages state back to its initial value (the welcome message)
    setMessages([
      {
        text: "Hi friend! Ask me some questions about our fab book database!",
        isUser: false,
      },
    ]);
    // Clear the input field as well
    setInput("");
    // Optional: if you have a loading state, reset it too
    // setIsSending(false); 
  };


  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
  // 1. Get the origin of the page the browser is currently on.
  //    e.g., "https://host-1-3000-6cb76hfzmouw.env.play.instruqt.com"
  const frontendOrigin = window.location.origin;

  // 2. Replace the frontend port number (3000) with the backend port number (8000)
  //    to construct the correct backend base URL.
  const backendBaseUrl = frontendOrigin.replace('-3000-', '-8000-');

  // 3. Construct the full API URL.
  const apiUrl = `${backendBaseUrl}/api/books-chat`;

  // Add a console log to see the URL you're about to use.
  console.log("Contacting backend at:", apiUrl);

  // 4. Use the dynamic apiUrl in your fetch call.
  const res = await fetch(apiUrl, {
    method: "POST",
    credentials: "include",
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
            <button onClick={handleClearChat} className="clear-button">
        Clear Chat
      </button>
    </div>
  );


}


