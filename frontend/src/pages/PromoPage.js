import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./PromoPage.css";

export default function PromoPage() {
  const navigate = useNavigate();
  const observerRef = useRef(null);

  // Get theme from localStorage or default to light
  const [theme, setTheme] = React.useState(() => {
    return localStorage.getItem("protego-theme") || "light";
  });

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("protego-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === "light" ? "dark" : "light"));
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

  const handleGetStarted = () => {
    navigate("/detect");
  };

  return (
    <div className="promo-container">
      {/* Navigation */}
      <nav className="promo-nav">
        <div className="nav-left">
          <div className="nav-logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <img src="/logo.png" alt="Protego Logo" className="logo-img" />
            <span className="logo-text">Protego</span>
          </div>
        </div>

        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#extension">Extension</a>
          <a href="#download">Download</a>
        </div>

        <div className="promo-nav-right">
          <div className="pill-container">
            <button className="theme-toggle" onClick={toggleTheme}>
              <span style={{ opacity: theme === 'dark' ? 1 : 0.3 }}>🌙</span>
              <span style={{ opacity: theme === 'light' ? 1 : 0.3 }}>☀️</span>
            </button>
          </div>
          <button className="nav-login-btn" onClick={handleGetStarted}>
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content animate-on-scroll">
          <div className="hero-badge">
            ✨ AI-Powered Scam Detection
          </div>

          <h1 className="hero-title">
            Protect Yourself with <span className="highlight">Protego</span>
          </h1>

          <p className="hero-subtitle">
            Taglish scam detection powered by mBERT with early-fusion metadata
            integration. Specifically designed for Facebook (via manual scanning) 
            and X/Twitter (via the automatic browser extension).
          </p>

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

          <div className="hero-stats">
            <div className="stat-item">
              <span className="stat-number">95%</span>
              <span className="stat-label">Detection Accuracy</span>
            </div>
          </div>
        </div>

        <div className="hero-visual animate-on-scroll">
          <div className="laptop-container">
            <img src="/laptop-mockup.png" alt="Laptop Mockup" className="laptop-img" />

            <div className="floating-scan-card">
              <div className="card-header">Scan Result</div>
              <div className="card-body">
                <div className="card-icon">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ width: "28px", height: "28px" }}
                  >
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    <path d="M9 12l2 2 4-4" />
                  </svg>
                </div>
                <div className="card-status">Legit</div>
                <div className="card-score">
                  Confidence Score
                  <strong>95%</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="section features-section">
        <h2 className="section-title animate-on-scroll">Why Protego?</h2>
        <div className="features-grid">
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon-wrapper">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"></path><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"></path><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"></path><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"></path><path d="M6.002 5.125A3 3 0 0 0 6.401 6.5"></path><path d="M3.477 10.896a4 4 0 0 1 .585-.396"></path><path d="M19.938 10.5a4 4 0 0 1 .585.396"></path><path d="M6 18a4 4 0 0 1-1.967-.516"></path><path d="M19.967 17.484A4 4 0 0 1 18 18"></path></svg>
              </div>
            </div>
            <h3>Multimodal Fusion</h3>
            <p>
              Combines mBERT text understanding with QR code and metadata
              signals for more accurate scam detection.
            </p>
          </div>
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon-wrapper">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
              </div>
            </div>
            <h3>Taglish Support</h3>
            <p>
              Trained on Tagalog, English, and Taglish text for Philippine
              social media.
            </p>
          </div>
          <div className="feature-card animate-on-scroll">
            <div className="feature-icon-wrapper">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
              </div>
            </div>
            <h3>Real-time Analysis</h3>
            <p>
              Get instant results with our optimized API pipeline and
              early-fusion model.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="section how-it-works-section">
        <h2 className="section-title animate-on-scroll">How It Works</h2>
        <div className="steps-container">
          <div className="step-card animate-on-scroll">
            <div className="step-number">1</div>
            <div className="step-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><rect x="7" y="7" width="3" height="3"></rect><rect x="14" y="7" width="3" height="3"></rect><rect x="7" y="14" width="3" height="3"></rect><rect x="14" y="14" width="3" height="3"></rect></svg>
            </div>
            <h3>Enter Post Text & QR</h3>
            <p>Paste the post or tweet, and any linked QR code or image.</p>
          </div>

          <div className="step-arrow animate-on-scroll">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
          </div>

          <div className="step-card animate-on-scroll">
            <div className="step-number">2</div>
            <div className="step-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"></path><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"></path><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"></path></svg>
            </div>
            <h3>Analyze Multimodal Signals</h3>
            <p>
              Our early-fusion model processes text, QR, and metadata
              together.
            </p>
          </div>

          <div className="step-arrow animate-on-scroll">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
          </div>

          <div className="step-card animate-on-scroll">
            <div className="step-number">3</div>
            <div className="step-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></svg>
            </div>
            <h3>Get Verdict</h3>
            <p>Receive scam/legit classification with confidence score.</p>
          </div>
        </div>
      </section>

      {/* Extension Features */}
      <section id="extension" className="section extension-section">
        <h2 className="section-title animate-on-scroll">
          Browser Extension
        </h2>
        <div className="extension-grid">
          <div className="extension-card animate-on-scroll">
            <div className="ext-icon-letter">S</div>
            <h4>Auto-Detect</h4>
            <p>Automatically scans posts on X (Twitter) as you browse. (Use the manual detection fallback for Facebook).</p>
            <div className="ext-badges">
              <span className="ext-badge">Facebook</span>
              <span className="ext-badge">X (Twitter)</span>
            </div>
          </div>
          <div className="extension-card animate-on-scroll">
            <div className="ext-icon-letter">D</div>
            <h4>Dashboard</h4>
            <p>View total scans and trends from our detection dashboard.</p>
            <div className="ext-badges">
              <span className="ext-badge">Analytics</span>
              <span className="ext-badge">Reports</span>
            </div>
          </div>
          <div className="extension-card animate-on-scroll">
            <div className="ext-icon-letter">P</div>
            <h4>Real-time Protection</h4>
            <p>Get instant alerts when potential scams are detected.</p>
            <div className="ext-badges">
              <span className="ext-badge">Alerts</span>
              <span className="ext-badge">Safety</span>
            </div>
          </div>
          <div className="extension-card animate-on-scroll">
            <div className="ext-icon-letter">H</div>
            <h4>History</h4>
            <p>Review your detection history and past scams.</p>
            <div className="ext-badges">
              <span className="ext-badge">Logs</span>
              <span className="ext-badge">Export</span>
            </div>
          </div>
        </div>
      </section>

      {/* Download Extension */}
      <section id="download" className="section download-section">
        <div className="download-card animate-on-scroll">
          <div className="dl-icon-circle">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
          </div>
          <h3>Download Extension</h3>
          <p>
            The Protego browser extension runs quietly in the background while
            you browse Facebook and X. It automatically scans posts and QR codes
            in real time, helps keep you safe by detecting scams before you click, and
            logs every detection to your dashboard and history so you can review what was caught.
          </p>
          <a className="download-btn" href="/protego-extension.zip" download>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ width: "18px", height: "18px" }}
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download Protego Extension (.zip)
          </a>
        </div>

        <h3 className="section-title animate-on-scroll" style={{ fontSize: "1.5rem" }}>
          How to Install &amp; Use It
        </h3>

        <div className="install-steps">
          <div className="install-step-row animate-on-scroll">
            <div className="install-num">1</div>
            <div className="install-text">
              <h4>Download and unzip</h4>
              <p>
                Click "Download Protego Extension" above and extract the downloaded .zip file to a folder on your computer.
              </p>
            </div>
            <div className="install-tag">Easy</div>
          </div>

          <div className="install-step-row animate-on-scroll">
            <div className="install-num">2</div>
            <div className="install-text">
              <h4>Open your browser's extensions page</h4>
              <p>
                In Chrome or Edge, go to chrome://extensions or edge://extensions, then enable Developer mode.
              </p>
            </div>
            <div className="install-tag">Developer</div>
          </div>

          <div className="install-step-row animate-on-scroll">
            <div className="install-num">3</div>
            <div className="install-text">
              <h4>Turn on Developer mode</h4>
              <p>
                Toggle "Developer mode" on — this lets you load unpacked extensions into your browser.
              </p>
            </div>
            <div className="install-tag">Settings</div>
          </div>

          <div className="install-step-row animate-on-scroll">
            <div className="install-num">4</div>
            <div className="install-text">
              <h4>Load the unpacked extension</h4>
              <p>
                Click "Load unpacked" and select the folder you extracted in step 1. Protego will appear in your extensions list.
              </p>
            </div>
            <div className="install-tag">Load</div>
          </div>

          <div className="install-step-row animate-on-scroll">
            <div className="install-num">5</div>
            <div className="install-text">
              <h4>Pin it to your toolbar</h4>
              <p>
                Click the puzzle icon in your browser toolbar and pin Protego so it's always one click away.
              </p>
            </div>
            <div className="install-tag">Quick</div>
          </div>

          <div className="install-step-row animate-on-scroll">
            <div className="install-num">6</div>
            <div className="install-text">
              <h4>Browse safely, get alerts</h4>
              <p>
                Visit Facebook or X as usual. Protego automatically scans posts and QR codes, flags suspicious content in real time, and logs the results — all from the toolbar icon while you type!
              </p>
            </div>
            <div className="install-tag">Protected</div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="promo-footer">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="footer-logo">
              <img src="/logo.png" alt="Protego Logo" className="footer-logo-img" />
              Protego
            </div>
            <p>AI-powered scam detection for a safer online community.</p>
            <div className="footer-socials">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="4" x2="20" y2="20"></line><line x1="20" y1="4" x2="4" y2="20"></line></svg>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
            </div>
          </div>

          <div className="footer-col">
            <h5>Product</h5>
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#extension">Extension</a>
            <a href="#download">Download</a>
          </div>

          <div className="footer-col">
            <h5>Support</h5>
            <a href="#">Help Center</a>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Contact Us</a>
          </div>

          <div className="footer-col">
            <h5>Company</h5>
            <a href="#">About Us</a>
            <a href="#">Blog</a>
            <a href="#">Careers</a>
          </div>

          <div className="footer-newsletter">
            <h5>Stay Updated</h5>
            <p>Get the latest updates and safety tips straight to your inbox.</p>
            <div className="newsletter-form">
              <input type="email" placeholder="Enter your email" />
              <button>→</button>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          © 2026 Protego. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
