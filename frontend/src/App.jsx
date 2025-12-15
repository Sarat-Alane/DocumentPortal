import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import "./App.css"

function App() {
  return (
    <Router>
      <Routes>
        {/* <Route path="/" element={<h1>Welcome to OCR Automation System</h1>} /> */}
        <Route path="/" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
