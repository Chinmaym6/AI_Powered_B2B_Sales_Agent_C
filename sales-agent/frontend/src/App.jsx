import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './components/Dashboard';
import CampaignDetails from './components/CampaignDetails';
import CreateCampaign from './pages/CreateCampaign';
import AllCampaignsPage from './pages/AllCampaignsPage';
import { CampaignProvider } from './context/CampaignContext';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('token');
    if (!token) {
        return <Navigate to="/login" replace />;
    }
    return children;
};

// Public Route Component (redirects to dashboard if logged in)
const PublicRoute = ({ children }) => {
    const token = localStorage.getItem('token');
    if (token) {
        return <Navigate to="/dashboard" replace />;
    }
    return children;
};

function App() {
    return (
        <CampaignProvider>
            <Router>
                <div className="min-h-screen bg-[#030303]">
                    <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="/login" element={
                            <PublicRoute>
                                <LoginPage />
                            </PublicRoute>
                        } />
                        <Route path="/register" element={
                            <PublicRoute>
                                <RegisterPage />
                            </PublicRoute>
                        } />

                        {/* Protected Routes */}
                        <Route path="/dashboard" element={
                            <ProtectedRoute>
                                <Dashboard />
                            </ProtectedRoute>
                        } />
                        <Route path="/campaigns/new" element={
                            <ProtectedRoute>
                                <CreateCampaign />
                            </ProtectedRoute>
                        } />
                        <Route path="/campaigns/all" element={
                            <ProtectedRoute>
                                <AllCampaignsPage />
                            </ProtectedRoute>
                        } />
                        <Route path="/campaign/:campaignId" element={
                            <ProtectedRoute>
                                <CampaignDetails />
                            </ProtectedRoute>
                        } />
                    </Routes>
                </div>
            </Router>
        </CampaignProvider>
    );
}

export default App;
