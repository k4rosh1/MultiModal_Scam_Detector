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
      { threshold: 0.1 }
    );

    document.querySelectorAll(".animate-on-scroll").forEach((el) => {
      observer.observe(el);
    });

    observerRef.current = observer;

    return () => observer.disconnect();
  }, []);

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
            Protect Yourself with{" "}
            <span className="highlight">Protego</span>
          </h1>

          <p className="hero-subtitle animate-on-scroll">
            Taglish scam detection powered by mBERT text-only model.
            Instantly analyze Facebook and X posts for accurate scam classification.
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
        <h2 className="section-title animate-on-scroll">
          Why Protego?
        </h2>
        <div className="features-grid">
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon">T</div>
            <h3>mBERT Text-Only</h3>
            <p>
              Uses mBERT multilingual model to analyze text content for
              scam detection without metadata.
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
              efficient text-only model.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="how-it-works-section">
        <h2 className="section-title animate-on-scroll">
          How It Works
        </h2>
        <div className="steps-container">
          <div className="step animate-on-scroll">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>Enter Post Text</h3>
              <p>Paste the post or tweet you want to analyze.</p>
            </div>
          </div>
          <div className="step-arrow animate-on-scroll">→</div>
          <div className="step animate-on-scroll">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>Analyze Text</h3>
              <p>Our mBERT model processes the text for scam indicators.</p>
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

      {/* Footer */}
      <footer className="promo-footer animate-on-scroll">
        <p>
          Protego — mBERT · Text-Only · Taglish
        </p>
        <p style={{ marginTop: 8, fontSize: 12, color: "var(--promo-text-muted)" }}>
          Built for Philippine social media scam detection
        </p>
        <p style={{ marginTop: 4, fontSize: 11, color: "var(--promo-text-muted)", fontStyle: "italic" }}>
          "Protego" — Latin for "I protect"
        </p>
      </footer>
    </div>
  );
}