import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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

function resolveFileUrl(src) {
  if (!src) return src;
  if (
    src.startsWith("http://") ||
    src.startsWith("https://") ||
    src.startsWith("data:") ||
    src.startsWith("mailto:") ||
    src.startsWith("#")
  ) {
    return src;
  }
  let cleanPath = src.trim().replace(/^["']|["']$/g, "");
  if (cleanPath.startsWith("file:///")) cleanPath = cleanPath.slice(8);
  else if (cleanPath.startsWith("file://")) cleanPath = cleanPath.slice(7);

  cleanPath = cleanPath.replace(/\\/g, "/");

  return `${API_BASE}/files?path=${encodeURIComponent(cleanPath)}`;
}

function getFileMeta(filePath, customName) {
  let clean = filePath || "";
  try {
    const url = new URL(clean, "http://localhost");
    if (url.searchParams.has("path")) {
      clean = url.searchParams.get("path");
    }
  } catch {}

  const basename =
    clean.split(/[/\\]/).filter(Boolean).pop() || customName || "file";
  const ext = (basename.includes(".") ? basename.split(".").pop() : "").toLowerCase();

  let category = "document";
  let typeLabel = ext ? ext.toUpperCase() : "File";
  let colorClass = "file-icon-doc";

  if (["png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "ico"].includes(ext)) {
    category = "image";
    typeLabel = `Image · ${ext.toUpperCase()}`;
    colorClass = "file-icon-img";
  } else if (
    [
      "py",
      "js",
      "jsx",
      "ts",
      "tsx",
      "html",
      "css",
      "json",
      "c",
      "cpp",
      "java",
      "rs",
      "go",
      "sql",
      "sh",
      "bat",
      "ps1",
    ].includes(ext)
  ) {
    category = "code";
    typeLabel = `Code · ${ext.toUpperCase()}`;
    colorClass = "file-icon-code";
  } else if (["txt", "md", "pdf", "doc", "docx", "rtf", "odt"].includes(ext)) {
    category = "document";
    typeLabel =
      ext === "txt"
        ? "Text · TXT"
        : ext === "pdf"
        ? "Document · PDF"
        : `Document · ${ext.toUpperCase()}`;
    colorClass = "file-icon-doc";
  } else if (["csv", "xls", "xlsx", "tsv"].includes(ext)) {
    category = "spreadsheet";
    typeLabel = `Spreadsheet · ${ext.toUpperCase()}`;
    colorClass = "file-icon-data";
  } else if (["zip", "rar", "7z", "tar", "gz"].includes(ext)) {
    category = "archive";
    typeLabel = `Archive · ${ext.toUpperCase()}`;
    colorClass = "file-icon-archive";
  } else if (["mp3", "wav", "m4a", "flac", "ogg"].includes(ext)) {
    category = "audio";
    typeLabel = `Audio · ${ext.toUpperCase()}`;
    colorClass = "file-icon-audio";
  } else if (["mp4", "mkv", "avi", "mov", "webm"].includes(ext)) {
    category = "video";
    typeLabel = `Video · ${ext.toUpperCase()}`;
    colorClass = "file-icon-video";
  }

  return { basename, ext, category, typeLabel, colorClass, rawPath: clean };
}

function FileCategoryIcon({ category }) {
  switch (category) {
    case "image":
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      );
    case "code":
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      );
    case "spreadsheet":
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M3 15h18M9 3v18" />
        </svg>
      );
    case "archive":
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="21 8 21 21 3 21 3 8" />
          <rect x="1" y="3" width="22" height="5" />
          <line x1="10" y1="12" x2="14" y2="12" />
        </svg>
      );
    case "audio":
    case "video":
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="5 3 19 12 5 21 5 3" />
        </svg>
      );
    default:
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
      );
  }
}

function FileCard({ href, name }) {
  const meta = getFileMeta(href, name);
  const downloadUrl = href.startsWith("http") ? href : resolveFileUrl(href);

  const handleOpen = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api(`/files/open?path=${encodeURIComponent(meta.rawPath)}`, {
        method: "POST",
      });
    } catch {
      window.open(downloadUrl, "_blank");
    }
  };

  const handleDownload = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = meta.basename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="claude-file-card" onClick={handleOpen} role="button" tabIndex={0}>
      <div className={`file-card-icon-box ${meta.colorClass}`}>
        <FileCategoryIcon category={meta.category} />
      </div>
      <div className="file-card-info">
        <span className="file-card-title" title={meta.rawPath}>
          {meta.basename}
        </span>
        <span className="file-card-subtitle">{meta.typeLabel}</span>
      </div>
      <div className="file-card-actions">
        <button
          type="button"
          className="file-card-action-btn open-btn"
          onClick={handleOpen}
          title="Open with default desktop app"
        >
          Open ↗
        </button>
        <button
          type="button"
          className="file-card-action-btn download-btn"
          onClick={handleDownload}
          title="Download file"
        >
          Download ⭳
        </button>
      </div>
    </div>
  );
}

function preprocessMessageContent(content) {
  if (!content) return "";

  // 1. Normalize Windows backslashes inside existing Markdown image tags: ![alt](C:\path\file.png) -> ![alt](C:/path/file.png)
  let text = content.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, url) => {
    const cleanUrl = url.trim().replace(/\\/g, "/");
    return `![${alt}](${cleanUrl})`;
  });

  // 2. Normalize Windows backslashes inside existing Markdown link tags: [name](C:\path\file.ext) -> [name](C:/path/file.ext)
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, name, url) => {
    const cleanUrl = url.trim().replace(/\\/g, "/");
    return `[${name}](${cleanUrl})`;
  });

  // 3. Convert standalone or backticked Windows file paths that are NOT already inside a Markdown link
  // e.g., `C:\Users\...\good.txt` or Path: C:\Users\...\good.txt
  const standaloneFileRegex =
    /(?<!\()(?<!\]\()(?<!\[)(?:`\s*)?([A-Za-z]:[\\/][^\s\n"'\(\)`]+\.([a-zA-Z0-9]{1,10}))(?:\s*`)?(?!\))/gi;

  text = text.replace(standaloneFileRegex, (match, fullPath, ext) => {
    const normalized = fullPath.replace(/\\/g, "/");
    const filename = normalized.split("/").pop();
    const lowerExt = (ext || "").toLowerCase();

    // If it's an image and not already formatted, make image tag
    if (["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(lowerExt)) {
      if (!text.includes(`](${normalized})`)) {
        return `\n\n![${filename}](${normalized})\n\n`;
      }
      return match;
    }

    // For any document/code/data file, turn into Markdown file link [filename](path)
    if (!text.includes(`](${normalized})`)) {
      return `\n\n[${filename}](${normalized})\n\n`;
    }
    return match;
  });

  return text;
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
  const [previewImage, setPreviewImage] = useState(null);

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  const activeConversation = useMemo(
    () => conversations.find((chat) => chat.id === conversationId),
    [conversations, conversationId],
  );

  const markdownComponents = useMemo(
    () => ({
      img({ src, alt }) {
        if (!src) return null;
        const fileUrl = resolveFileUrl(src);
        if (!fileUrl) return null;

        return (
          <div className="chat-image-card">
            <img
              src={fileUrl}
              alt={alt || "Screenshot / Image"}
              className="chat-inline-img"
              onClick={() => setPreviewImage(fileUrl)}
              onError={(e) => {
                console.error("Failed to load image from:", fileUrl);
                e.currentTarget.style.display = "none";
              }}
            />
            <div className="chat-image-meta">
              <span className="chat-image-title">{alt || "Image preview"}</span>
              <button
                type="button"
                className="chat-image-open-btn"
                onClick={() => window.open(fileUrl, "_blank")}
              >
                ↗ Open
              </button>
            </div>
          </div>
        );
      },
      code({ inline, className, children, ...props }) {
        const match = /language-(\w+)/.exec(className || "");
        const codeText = String(children).replace(/\n$/, "");
        return !inline ? (
          <div className="code-block-container">
            <div className="code-block-header">
              <span>{match ? match[1] : "code"}</span>
              <button
                type="button"
                className="copy-code-btn"
                onClick={() => navigator.clipboard.writeText(codeText)}
              >
                Copy
              </button>
            </div>
            <pre className="code-block-body">
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          </div>
        ) : (
          <code className="inline-code" {...props}>
            {children}
          </code>
        );
      },
      a({ href, children }) {
        if (!href) return <a>{children}</a>;

        // Check if this link points to a file or file endpoint
        const isFileLink =
          href.includes("/files?path=") ||
          /^[A-Za-z]:[/\\]/i.test(href) ||
          href.startsWith("file://") ||
          /\.([a-zA-Z0-9]{1,6})($|\?)/.test(href);

        if (isFileLink) {
          const fileName = typeof children === "string" ? children : "";
          return <FileCard href={href} name={fileName} />;
        }

        return (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="chat-link"
          >
            {children}
          </a>
        );
      },
    }),
    [],
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
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={markdownComponents}
                        urlTransform={(url) => resolveFileUrl(url)}
                      >
                        {preprocessMessageContent(message.content)}
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

      {previewImage && (
        <div
          className="image-modal-overlay"
          onClick={() => setPreviewImage(null)}
        >
          <div
            className="image-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="image-modal-close"
              onClick={() => setPreviewImage(null)}
            >
              ×
            </button>
            <img src={previewImage} alt="Expanded preview" />
          </div>
        </div>
      )}

    </div>
  );
}

export default App;