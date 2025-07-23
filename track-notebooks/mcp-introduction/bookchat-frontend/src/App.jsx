import { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";
import elasticLogo from "/elastic.svg";

export default function App() {
  const [messages, setMessages] = useState(() => {
    const stored = localStorage.getItem("bookchat-history");
    return stored
      ? JSON.parse(stored)
      : [
          {
            role: "assistant",
            text: "Hi friend! Ask me some questions about our fab book database!",
            tool: null,
          },
        ];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    const trimmed = messages.slice(-20);
    localStorage.setItem("bookchat-history", JSON.stringify(trimmed));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleClear = () => {
    setMessages([
      {
        role: "assistant",
        text: "Hi friend! Ask me some questions about our fab book database!",
        tool: null,
      },
    ]);
    setInput("");
    setLoading(false);
  };

  const parseToolFromResponse = (responseText) => {
    const prefix = "Using the ";
    const suffix = " tool, ";
    let toolUsed = null;
    let cleanText = responseText;

    if (
      responseText.startsWith(prefix) &&
      responseText.includes(suffix)
    ) {
      const start = prefix.length;
      const end = responseText.indexOf(suffix);
      toolUsed = responseText.substring(start, end);
      cleanText = responseText
        .substring(end + suffix.length)
        .trim();
      cleanText = cleanText.charAt(0).toUpperCase() + cleanText.slice(1);
    }

    return { toolUsed, cleanText };
  };

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    setMessages((m) => [
      ...m,
      { role: "user", text: input, tool: null },
    ]);
    setInput("");
    setLoading(true);

    try {
      const frontendOrigin = window.location.origin;
      const backendBaseUrl = frontendOrigin.replace(
        "-3000-",
        "-8000-"
      );
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
        throw new Error(`Status ${res.status}`);
      }

      const data = await res.json();
      const { toolUsed, cleanText } = parseToolFromResponse(
        data.response || ""
      );
      const finalText = cleanText || data.response;
      const tool = toolUsed || data.tool_used || null;

      setMessages((m) => [
        ...m,
        { role: "assistant", text: finalText, tool },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: "Sorry, an error occurred.",
          tool: "Error",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-title">
        <img
          src={elasticLogo}
          alt="Elastic"
          className="elastic-logo"
        />
        Elastic Book Chat
      </h2>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-header">
              <strong>
                {msg.role === "user" ? "You:" : "Assistant:"}
              </strong>
              {msg.tool && (
                <span className="tool-indicator">{msg.tool}</span>
              )}
            </div>

            {[
              "search",
              "search_google_books",
              "get_shards",
              "get_mappings",
              "list_indices",
            ].includes(msg.tool) ? (
              <LookupRenderer markdown={msg.text} />
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.text}
              </ReactMarkdown>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-header">
              <strong>Assistant:</strong>
            </div>
            <div className="typing-indicator">
              <span />
              <span />
              <span />
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
          placeholder="Ask me about books..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>

      <button className="clear-button" onClick={handleClear}>
        Clear Chat
      </button>
    </div>
  );
}

function LookupRenderer({ markdown }) {
  const text = markdown || "";
  const [before, after = ""] = text.split(/Additional Notes:/);
  const firstNum = before.search(/\d+\.\s/);
  const intro =
    firstNum > 0
      ? before.slice(0, firstNum).trim()
      : before.trim();

  const entries = [];
  const re = /(\d+\.\s[\s\S]*?)(?=\n\d+\.|\s*$)/g;
  let m,
    lastEnd = firstNum > 0 ? firstNum : 0;
  while ((m = re.exec(before))) {
    const raw = m[1].trim().replace(/^\d+\.\s*/, "");
    entries.push(raw);
    lastEnd = m.index + m[1].length;
  }

  const trailing = before.slice(lastEnd).trim();

  return (
    <>
      {(intro || trailing) && (
        <div className=".message assistant">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {intro + (trailing ? `\n\n${trailing}` : "")}
          </ReactMarkdown>
        </div>
      )}

      <div className="book-list">
        {entries.map((entryMd, i) => (
          <div key={i} className="book-card">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: (p) => <p {...p} />,
                a: (a) => <a className="lookup-link" {...a} />,
                ul: (ul) => (
                  <ul style={{ listStyle: "none", margin: 0, padding: 0 }} {...ul} />
                ),
                li: (li) => <li style={{ marginBottom: "0.5em" }} {...li} />,
              }}
            >
              {entryMd}
            </ReactMarkdown>
          </div>
        ))}
      </div>

      {after.trim() && (
        <div className=".message assistant">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {after.trim()}
          </ReactMarkdown>
        </div>
      )}
    </>
  );
}
