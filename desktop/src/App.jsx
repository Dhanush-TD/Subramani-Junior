import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = "Request failed";

    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Ignore non-JSON error bodies.
    }

    throw new Error(`${response.status}: ${detail}`);
  }

  return response.json();
}

function Icon({ children, className = "" }) {
  return <span className={`icon ${className}`}>{children}</span>;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [backendOnline, setBackendOnline] = useState(false);

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  const activeConversation = useMemo(
    () => conversations.find((chat) => chat.id === conversationId),
    [conversations, conversationId],
  );

  // ---------------------------------------
  // API: Load conversations
  // ---------------------------------------
  const refreshConversations = async () => {
    const chats = await api("/chats");
    setConversations(chats);
    return chats;
  };

  // ---------------------------------------
  // API: Load one conversation
  // ---------------------------------------
  const loadConversation = async (id) => {
    const history = await api(`/chats/${id}/messages`);

    setConversationId(id);
    setMessages(history);
  };

  // ---------------------------------------
  // Initialize & Health Polling
  // ---------------------------------------
  const initialize = async () => {
    try {
      await api("/health");
      setBackendOnline(true);

      let chats = await refreshConversations();

      if (chats.length === 0) {
        const created = await api("/chats", {
          method: "POST",
        });

        chats = [created];
        setConversations(chats);
      }

      if (chats.length > 0) {
        await loadConversation(chats[0].id);
      }
      return true;
    } catch (error) {
      console.error("Backend connection failed:", error);
      setBackendOnline(false);
      return false;
    } finally {
      setInitializing(false);
    }
  };

  useEffect(() => {
    initialize();

    const interval = setInterval(async () => {
      try {
        await api("/health");
        setBackendOnline((prev) => {
          if (!prev) {
            initialize();
          }
          return true;
        });
      } catch {
        setBackendOnline(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // ---------------------------------------
  // Auto scroll
  // ---------------------------------------
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  // ---------------------------------------
  // Focus textarea
  // ---------------------------------------
  useEffect(() => {
    if (!loading) {
      textareaRef.current?.focus();
    }
  }, [loading, conversationId]);

  // ---------------------------------------
  // Create new chat
  // ---------------------------------------
  const createNewChat = async () => {
    try {
      const created = await api("/chats", {
        method: "POST",
      });

      setConversations((prev) => [created, ...prev]);
      setConversationId(created.id);
      setMessages([]);
      setInput("");

      requestAnimationFrame(() => {
        textareaRef.current?.focus();
      });
    } catch (error) {
      console.error("Could not create chat:", error);
    }
  };

  // ---------------------------------------
  // Select existing chat
  // ---------------------------------------
  const selectChat = async (id) => {
    if (loading || id === conversationId) {
      return;
    }

    try {
      await loadConversation(id);
    } catch (error) {
      console.error("Could not load conversation:", error);
    }
  };

  // ---------------------------------------
  // Save message to SQLite
  // ---------------------------------------
  const saveMessage = async (id, role, content) => {
    await api(`/chats/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({
        role,
        content,
      }),
    });
  };

  // ---------------------------------------
  // Send message
  // ---------------------------------------
  const sendMessage = async () => {
    const text = input.trim();

    if (!text || loading || !conversationId) {
      return;
    }

    setInput("");
    setLoading(true);

    // Show user message immediately
    const userMessage = {
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      // -----------------------------------
      // 1. Save user message
      // -----------------------------------
      await saveMessage(
        conversationId,
        "user",
        text,
      );

      // -----------------------------------
      // 2. Send message to AI backend
      //
      // IMPORTANT:
      // conversation_id is required here.
      // -----------------------------------
      const data = await api("/chat", {
        method: "POST",
        body: JSON.stringify({
          conversation_id: conversationId,
          message: text,
        }),
      });

      // -----------------------------------
      // 3. Display assistant response
      // -----------------------------------
      const assistantMessage = {
        role: "assistant",
        content: data.response,
      };

      setMessages((prev) => [
        ...prev,
        assistantMessage,
      ]);

      // -----------------------------------
      // 4. Save assistant response
      // -----------------------------------
      await saveMessage(
        conversationId,
        "assistant",
        data.response,
      );

      // -----------------------------------
      // 5. Automatically create title
      // -----------------------------------
      if (activeConversation?.title === "New Chat") {
        const title =
          text.length > 40
            ? `${text.slice(0, 40)}…`
            : text;

        await api(
          `/chats/${conversationId}/title`,
          {
            method: "PATCH",
            body: JSON.stringify({
              title,
            }),
          },
        );
      }

      // -----------------------------------
      // 6. Refresh sidebar
      // -----------------------------------
      await refreshConversations();
    } catch (error) {
      console.error("Chat request failed:", error);

      const errorText = backendOnline
        ? "The local AI agent could not complete the request. Check the backend terminal for the error."
        : "I couldn't connect to the local AI backend. Make sure FastAPI is running.";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorText,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------
  // Enter = Send
  // Shift + Enter = New line
  // ---------------------------------------
  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  };

  // ---------------------------------------
  // Auto resize textarea
  // ---------------------------------------
  const handleInput = (event) => {
    setInput(event.target.value);

    const textarea = event.target;

    textarea.style.height = "auto";

    textarea.style.height = `${Math.min(
      textarea.scrollHeight,
      180,
    )}px`;
  };

  // ---------------------------------------
  // UI
  // ---------------------------------------
  return (
    <div className="app-shell">

      {/* ================================
          SIDEBAR
      ================================= */}

      <aside className="sidebar">

        <div className="sidebar-top">

          <div className="brand-row">

            <div className="brand-mark">
              ✦
            </div>

            <span className="brand-name">
              Local AI Agent
            </span>

            <button
              className="icon-button sidebar-collapse"
              aria-label="Collapse sidebar"
            >
              <Icon>‹</Icon>
            </button>

          </div>

          <button
            className="new-chat"
            onClick={createNewChat}
          >
            <Icon>＋</Icon>

            <span>
              New chat
            </span>

            <span className="new-chat-shortcut">
              Ctrl K
            </span>
          </button>

          <div className="sidebar-tools">

            <button className="sidebar-tool">
              <Icon>⌕</Icon>

              <span>
                Search chats
              </span>

              <span className="tool-shortcut">
                Ctrl K
              </span>
            </button>

            <button className="sidebar-tool">
              <Icon>▱</Icon>

              <span>
                Library
              </span>
            </button>

            <button className="sidebar-tool">
              <Icon>□</Icon>

              <span>
                Projects
              </span>
            </button>

          </div>

        </div>

        {/* ================================
            RECENT CHATS
        ================================= */}

        <div className="recent-section">

          <div className="section-label">
            Recents
          </div>

          <div className="recent-list">

            {conversations.length === 0 ? (
              <div className="empty-recents">
                No conversations yet
              </div>
            ) : (
              conversations.map((chat) => (
                <button
                  key={chat.id}
                  className={`recent-chat ${
                    chat.id === conversationId
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    selectChat(chat.id)
                  }
                  title={
                    chat.title || "New Chat"
                  }
                >
                  <Icon>◌</Icon>

                  <span>
                    {chat.title || "New Chat"}
                  </span>
                </button>
              ))
            )}

          </div>

        </div>

        {/* ================================
            SIDEBAR BOTTOM
        ================================= */}

        <div className="sidebar-bottom">

          <button className="sidebar-tool settings-button">
            <Icon>⚙</Icon>

            <span>
              Settings
            </span>
          </button>

          <div className="account-row">

            <div className="account-avatar">
              D
            </div>

            <div
              className="account-info"
              onClick={initialize}
              style={{ cursor: "pointer" }}
              title={backendOnline ? "Online" : "Offline - Click to reconnect"}
            >
              <strong>Local Agent</strong>
              <span style={{ color: backendOnline ? "inherit" : "#ef4444" }}>
                {backendOnline ? "Desktop assistant" : "Offline (click retry)"}
              </span>
            </div>

            <span
              onClick={initialize}
              style={{ cursor: "pointer" }}
              title={backendOnline ? "Online" : "Offline - Click to reconnect"}
              className={`status-dot ${
                backendOnline ? "online" : "offline"
              }`}
            />

          </div>

        </div>

      </aside>

      {/* ================================
          MAIN PANEL
      ================================= */}

      <main className="main-panel">

        {/* TOP BAR */}

        <header className="topbar">

          <div className="topbar-left">

            <span className="mobile-brand-mark">
              ✦
            </span>

            <span className="model-name">
              {activeConversation?.title ||
                "Local AI Agent"}
            </span>

            <span className="model-chevron">
              ⌄
            </span>

          </div>

          <div className="topbar-actions">

            <button
              className="topbar-button"
              aria-label="Share"
            >
              ↗
            </button>

            <button
              className="topbar-button"
              aria-label="More options"
            >
              •••
            </button>

          </div>

        </header>

        {/* ================================
            CHAT AREA
        ================================= */}

        <section className="chat-area">

          {initializing ? (

            <div className="welcome loading-welcome">

              <div className="welcome-logo">
                ✦
              </div>

              <h1>
                Starting local agent
              </h1>

              <p>
                Connecting to your local AI
                backend…
              </p>

            </div>

          ) : messages.length === 0 ? (

            <div className="welcome">

              <div className="welcome-logo">
                ✦
              </div>

              <h1>
                How can I help you today?
              </h1>

              <p>
                Ask your local AI agent to work
                with files, apps, code, and your
                desktop.
              </p>

              <div className="suggestions">

                <button
                  onClick={() =>
                    setInput("Find a file")
                  }
                >
                  Find a file
                </button>

                <button
                  onClick={() =>
                    setInput(
                      "Show my calendar events for tomorrow",
                    )
                  }
                >
                  Check calendar
                </button>

                <button
                  onClick={() =>
                    setInput(
                      "Open Notepad",
                    )
                  }
                >
                  Open an application
                </button>

                <button
                  onClick={() =>
                    setInput(
                      "Take a screenshot",
                    )
                  }
                >
                  Take a screenshot
                </button>

              </div>

            </div>

          ) : (

            <div className="messages">

              {messages.map(
                (message, index) => (

                  <div
                    key={`${
                      message.id ||
                      message.role
                    }-${index}`}
                    className={`message-row ${
                      message.role
                    } ${
                      message.error
                        ? "message-error"
                        : ""
                    }`}
                  >

                    {/* Assistant avatar */}

                    {message.role ===
                      "assistant" && (
                      <div className="avatar assistant-avatar">
                        ✦
                      </div>
                    )}

                    {/* Message */}

                    <div className="message-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                    </div>

                    {/* User avatar */}

                    {message.role ===
                      "user" && (
                      <div className="avatar user-avatar">
                        D
                      </div>
                    )}

                  </div>

                ),
              )}

              {/* Typing indicator */}

              {loading && (

                <div className="message-row assistant">

                  <div className="avatar assistant-avatar">
                    ✦
                  </div>

                  <div className="message-content typing">

                    <span />
                    <span />
                    <span />

                  </div>

                </div>

              )}

              <div ref={messagesEndRef} />

            </div>

          )}

        </section>

        {/* ================================
            COMPOSER
        ================================= */}

        <div className="composer-area">

          <div className="composer">

            <button
              className="composer-icon"
              aria-label="Add attachment"
            >
              ＋
            </button>

            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Message your local AI agent..."
              rows={1}
              disabled={
                initializing ||
                !backendOnline
              }
            />

            <button
              className={`send-button ${
                input.trim()
                  ? "ready"
                  : ""
              }`}
              onClick={sendMessage}
              disabled={
                !input.trim() ||
                loading ||
                !conversationId ||
                !backendOnline
              }
              aria-label="Send message"
            >
              ↑
            </button>

          </div>

          <div className="composer-hint">
            Local AI can make mistakes. Check
            important information.
          </div>

        </div>

      </main>

    </div>
  );
}

export default App;