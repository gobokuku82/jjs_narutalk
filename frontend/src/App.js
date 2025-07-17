import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import MainDashboard from './components/MainDashboard';
import ChatScreen from './components/ChatScreen';

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/" element={<MainDashboard />} />
          <Route path="/chat" element={<ChatScreen />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
