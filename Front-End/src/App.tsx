import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Analytics from './components/Analytics';
import FactChecker from './components/FactChecker';
import LoadingSpinner from './components/LoadingSpinner';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    if (authMode === 'login') {
      return (
        <Login
          switchToRegister={() => setAuthMode('register')}
        />
      );
    } else {
      return (
        <Register
          switchToLogin={() => setAuthMode('login')}
        />
      );
    }
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/fact-check" element={<FactChecker />} />
      </Routes>
    </Router>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
export default App;