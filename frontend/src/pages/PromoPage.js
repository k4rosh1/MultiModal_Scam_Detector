import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./PromoPage.css";

export default function PromoPage() {
  const navigate = useNavigate();
  const observerRef = useRef(null);

  // Get theme from localStorage or default to dark
  const [theme, setTheme] = React.useState(() => {
    return localStorage.getItem("protego-theme") || "dark";
  });

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("protego-theme", theme);
  }, [theme]);

  const toggleTheme = (newTheme) => {
    setTheme(newTheme);
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate");
          }
        });
      },
      { threshold: 0.1 },
    );

    document.querySelectorAll(".animate-on-scroll").forEach((el) => {
      observer.observe(el);
    });

    observerRef.current = observer;

    return () => observer.disconnect();
  }, []);

  // "Get Started" always launches the full multimodal detector
  const handleGetStarted = () => {
    navigate("/detect");
  };

  return (
    <div className="promo-container">
      {/* Navigation */}
      <nav className="promo-nav">
        <div className="nav-left">
          <div className="nav-logo" onClick={() => navigate("/")}>
            <span className="logo-icon">P</span>
            <span className="logo-text">Protego</span>
          </div>
        </div>

        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#extension">Extension</a>
          <a href="#download">Download</a>
        </div>

        <div className="nav-right">
          {/* Theme Toggle */}
          <div className="promo-theme-toggle">
            <button
              className={`promo-theme-btn ${theme === "light" ? "active" : ""}`}
              onClick={() => toggleTheme("light")}
            >
              Light
            </button>
            <button
              className={`promo-theme-btn ${theme === "dark" ? "active" : ""}`}
              onClick={() => toggleTheme("dark")}
            >
              Dark
            </button>
          </div>
          <button className="nav-login-btn" onClick={handleGetStarted}>
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section animate-on-scroll">
        <div className="hero-content">
          <div className="hero-badge animate-on-scroll">
            <span className="badge-dot">●</span>
            AI-Powered Scam Detection
          </div>

          <h1 className="hero-title animate-on-scroll">
            Protect Yourself with <span className="highlight">Protego</span>
          </h1>

          <p className="hero-subtitle animate-on-scroll">
            Multimodal Taglish scam detection powered by an mBERT early-fusion
            model. Instantly analyze Facebook and X posts — text, QR codes, and
            metadata — for accurate scam classification.
          </p>

          <div className="button-container animate-on-scroll">
            <button className="get-started-btn" onClick={handleGetStarted}>
              Get Started Now
              <svg
                className="arrow-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M5 12h14" />
                <path d="M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          <div className="hero-stats animate-on-scroll">
            <div className="stat-item">
              <span className="stat-number">50%</span>
              <span className="stat-label">Detection Accuracy</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <h2 className="section-title animate-on-scroll">Why Protego?</h2>
        <div className="features-grid">
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon">M</div>
            <h3>Multimodal Fusion</h3>
            <p>
              Combines mBERT text understanding with QR code and metadata
              signals for more accurate scam detection.
            </p>
          </div>
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon">L</div>
            <h3>Taglish Support</h3>
            <p>
              Trained on Tagalog, English, and Taglish text for Philippine
              social media.
            </p>
          </div>
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon">R</div>
            <h3>Real-time Analysis</h3>
            <p>
              Get instant results with our optimized API pipeline and
              early-fusion model.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="how-it-works-section">
        <h2 className="section-title animate-on-scroll">How It Works</h2>
        <div className="steps-container">
          <div className="step animate-on-scroll">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>Enter Post Text & QR</h3>
              <p>Paste the post or tweet, and any linked QR code or image.</p>
            </div>
          </div>
          <div className="step-arrow animate-on-scroll">→</div>
          <div className="step animate-on-scroll">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>Analyze Multimodal Signals</h3>
              <p>
                Our early-fusion model processes text, QR, and metadata
                together.
              </p>
            </div>
          </div>
          <div className="step-arrow animate-on-scroll">→</div>
          <div className="step animate-on-scroll">
            <div className="step-number">3</div>
            <div className="step-content">
              <h3>Get Verdict</h3>
              <p>Receive scam/legit classification with confidence score.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Extension Features */}
      <section id="extension" className="how-it-works-section">
        <div className="extension-features">
          <h2 className="extension-title animate-on-scroll">
            Browser Extension
          </h2>
          <div className="extension-grid">
            <div className="extension-card animate-on-scroll">
              <span className="extension-icon">S</span>
              <h4>Auto-Detect</h4>
              <p>Automatically scans posts as you browse Facebook and X.</p>
              <div className="extension-badge">
                <span className="badge-tag">Facebook</span>
                <span className="badge-tag">X (Twitter)</span>
              </div>
            </div>
            <div className="extension-card animate-on-scroll">
              <span className="extension-icon">D</span>
              <h4>Dashboard</h4>
              <p>View statistics and trends from all detected scams.</p>
              <div className="extension-badge">
                <span className="badge-tag">Analytics</span>
                <span className="badge-tag">Reports</span>
              </div>
            </div>
            <div className="extension-card animate-on-scroll">
              <span className="extension-icon">P</span>
              <h4>Real-time Protection</h4>
              <p>Get instant alerts when potential scams are detected.</p>
              <div className="extension-badge">
                <span className="badge-tag">Alerts</span>
                <span className="badge-tag">Safety</span>
              </div>
            </div>
            <div className="extension-card animate-on-scroll">
              <span className="extension-icon">H</span>
              <h4>History</h4>
              <p>Keep track of all detected scams in one place.</p>
              <div className="extension-badge">
                <span className="badge-tag">Logs</span>
                <span className="badge-tag">Export</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Download Extension */}
      <section id="download" className="download-section">
        <h2 className="section-title animate-on-scroll">Download Extension</h2>
        <div className="download-card animate-on-scroll">
          <p>
            The Protego browser extension runs quietly in the background while
            you browse Facebook and X. It automatically scans posts and QR codes
            in real time, flags likely scams directly on the page with a warning
            badge, and logs every detection to your Dashboard and History so you
            can review what was caught.
          </p>
          <a className="download-btn" href="/protego-extension.zip" download>
            <svg
              className="download-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download Protego Extension (.zip)
          </a>
        </div>

        <h3 className="tutorial-title animate-on-scroll">
          How to Install &amp; Use It
        </h3>
        <div className="tutorial-steps">
          <div className="tutorial-step animate-on-scroll">
            <div className="tutorial-step-number">1</div>
            <div className="tutorial-step-content">
              <h4>Download and unzip</h4>
              <p>
                Click "Download Protego Extension" above and extract the
                downloaded <code>protego-extension.zip</code> file to a folder
                you'll keep on your computer.
              </p>
            </div>
          </div>
          <div className="tutorial-step animate-on-scroll">
            <div className="tutorial-step-number">2</div>
            <div className="tutorial-step-content">
              <h4>Open your browser's extensions page</h4>
              <p>
                In Chrome or Edge, go to <code>chrome://extensions</code> (or{" "}
                <code>edge://extensions</code>) from the address bar.
              </p>
            </div>
          </div>
          <div className="tutorial-step animate-on-scroll">
            <div className="tutorial-step-number">3</div>
            <div className="tutorial-step-content">
              <h4>Turn on Developer mode</h4>
              <p>
                Toggle "Developer mode" on — it's usually in the top-right
                corner of the extensions page.
              </p>
            </div>
          </div>
          <div className="tutorial-step animate-on-scroll">
            <div className="tutorial-step-number">4</div>
            <div className="tutorial-step-content">
              <h4>Load the unpacked extension</h4>
              <p>
                Click "Load unpacked" and select the folder you extracted in
                step 1. Protego will appear in your extensions list and toolbar.
              </p>
            </div>
          </div>
          <div className="tutorial-step animate-on-scroll">
            <div className="tutorial-step-number">5</div>
            <div className="tutorial-step-content">
              <h4>Pin it to your toolbar</h4>
              <p>
                Click the puzzle-piece icon in your browser toolbar and pin
                Protego so it's always one click away.
              </p>
            </div>
          </div>
          <div className="tutorial-step animate-on-scroll">
            <div className="tutorial-step-number">6</div>
            <div className="tutorial-step-content">
              <h4>Browse and stay protected</h4>
              <p>
                Visit Facebook or X as usual. Protego automatically scans posts
                and QR codes, flags suspicious ones with a warning badge, and
                logs the results — click the toolbar icon anytime to see your
                Dashboard and History.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="promo-footer animate-on-scroll">
        <p>Protego — mBERT · Multimodal · Taglish</p>
        <p
          style={{
            marginTop: 8,
            fontSize: 12,
            color: "var(--promo-text-muted)",
          }}
        >
          Built for Philippine social media scam detection
        </p>
        <p
          style={{
            marginTop: 4,
            fontSize: 11,
            color: "var(--promo-text-muted)",
            fontStyle: "italic",
          }}
        >
          "Protego" — Latin for "I protect"
        </p>
      </footer>
    </div>
  );
}
