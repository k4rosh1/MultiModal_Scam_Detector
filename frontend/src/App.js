import React, { useEffect, useState, useRef } from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import DetectPage from "./pages/DetectPage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import PromoPage from "./pages/PromoPage";
import { checkHealth } from "./api";
import "./App.css";

function Navbar({ theme, toggleTheme }) {
  const [online, setOnline] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => {
    const check = () => checkHealth().then((ok) => setOnline(ok));

    function start() {
      timerRef.current = setInterval(check, 30000);
    }
    function stop() {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    function onVisibilityChange() {
      if (document.hidden) {
        stop();
      } else {
        check(); // immediate check on tab focus
        start();
      }
    }

    check();
    start();
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, []);

  return (
    <nav className={`navbar ${theme === 'light' ? 'navbar-light' : 'navbar-dark'}`}>
      <div className="navbar-brand">
        <div className="brand-icon">🛡</div>
        <div>
          <div className="brand-name">Protego</div>
          <div className="brand-sub">mBERT · Early Fusion · Taglish</div>
        </div>
      </div>

      <div className="navbar-links">
        <NavLink
          to="/"
          className={({ isActive }) =>
            isActive ? "nav-link active" : "nav-link"
          }
          end
        >
          🏠 Home
        </NavLink>
        <NavLink
          to="/detect"
          className={({ isActive }) =>
            isActive ? "nav-link active" : "nav-link"
          }
        >
          🔍 Detect
        </NavLink>
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            isActive ? "nav-link active" : "nav-link"
          }
        >
          📊 Dashboard
        </NavLink>
        <NavLink
          to="/history"
          className={({ isActive }) =>
            isActive ? "nav-link active" : "nav-link"
          }
        >
          🗂 History
        </NavLink>
      </div>

      <div className="navbar-right">
        <button
          className="theme-toggle"
          onClick={toggleTheme}
          title="Toggle light/dark mode"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
        <div className={`navbar-status ${online === false ? "offline" : ""}`}>
          <span
            className={`status-dot ${online === true ? "online" : online === false ? "offline" : ""}`}
          />
          <span>
            {online === null
              ? "Checking..."
              : online
                ? "API Online"
                : "API Offline"}
          </span>
        </div>
      </div>
    </nav>
  );
}

function AppContent({ theme, toggleTheme }) {
  const location = useLocation();
  // Hide navbar on Home (promo) page only - Detect page shows its own header with navbar
  const hideNavbar = location.pathname === "/";

  return (
    <>
      {!hideNavbar && <Navbar theme={theme} toggleTheme={toggleTheme} />}
      <main className={location.pathname === "/" ? "promo-main" : "app-main"}>
        <Routes>
          <Route path="/" element={<PromoPage />} />
          <Route path="/detect" element={<DetectPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("scamshield-theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("scamshield-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <BrowserRouter>
      <AppContent theme={theme} toggleTheme={toggleTheme} />
    </BrowserRouter>
  );
}