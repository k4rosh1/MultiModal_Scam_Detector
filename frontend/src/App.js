import React, { useEffect, useState, useRef } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  useLocation,
} from "react-router-dom";
import DetectPage from "./pages/DetectPage";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import MetricsPage from "./pages/MetricsPage";
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
    <nav className="navbar">
      <div className="navbar-left">
        <NavLink to="/" className="navbar-brand" title="Back to home">
          <img src="/logo.png" alt="Protego" className="dashboard-logo-img" />
          <span className="brand-name">Protego</span>
        </NavLink>
      </div>

      <div className="navbar-links">
        <NavLink to="/detect" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Detect</NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Dashboard</NavLink>
        <NavLink to="/metrics" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>Metrics</NavLink>
      </div>

      <div className="navbar-right">
        <div className="pill-container">
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title="Toggle light/dark mode"
          >
            <span style={{ opacity: theme === 'dark' ? 1 : 0.3 }}>🌙</span>
            <span style={{ opacity: theme === 'light' ? 1 : 0.3 }}>☀️</span>
          </button>
        </div>
        
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
  // Hide navbar on Home (promo/landing) page only - other pages show the navbar
  const hideNavbar = location.pathname === "/";

  return (
    <>
      {hideNavbar ? (
        <main className="promo-main">
          <Routes>
            <Route path="/" element={<PromoPage />} />
          </Routes>
        </main>
      ) : (
        <div className="app-wrapper">
          <Navbar theme={theme} toggleTheme={toggleTheme} />
          <main className="app-main">
            <Routes>
              <Route path="/detect" element={<DetectPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/metrics" element={<MetricsPage />} />
            </Routes>
          </main>
        </div>
      )}
    </>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("protego-theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("protego-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <BrowserRouter>
      <AppContent theme={theme} toggleTheme={toggleTheme} />
    </BrowserRouter>
  );
}
