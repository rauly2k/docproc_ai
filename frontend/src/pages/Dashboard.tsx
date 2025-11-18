/**
 * Dashboard Page
 * Main landing page after login
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCurrentUser, logout } from '../services/auth';
import { apiClient } from '../services/api';

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const currentUser = getCurrentUser();
      setUser(currentUser);

      try {
        // Fetch tenant stats
        const statsData = await apiClient.getTenantStats();
        setStats(statsData);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>DocProc AI</h1>
        <div className="user-info">
          <span>{user?.email}</span>
          <button onClick={handleLogout} className="btn-secondary">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-content">
        <h2>Welcome to Document AI Platform</h2>
        <p>Process, analyze, and interact with your documents using AI.</p>

        {loading ? (
          <div className="loading">Loading statistics...</div>
        ) : stats ? (
          <div className="stats-grid">
            <div className="stat-card">
              <h3>{stats.total_documents || 0}</h3>
              <p>Total Documents</p>
            </div>
            <div className="stat-card">
              <h3>{stats.total_invoices_processed || 0}</h3>
              <p>Invoices Processed</p>
            </div>
            <div className="stat-card">
              <h3>{stats.total_ocr_processed || 0}</h3>
              <p>OCR Processed</p>
            </div>
            <div className="stat-card">
              <h3>{stats.total_summaries_generated || 0}</h3>
              <p>Summaries Generated</p>
            </div>
            <div className="stat-card">
              <h3>{stats.total_rag_queries || 0}</h3>
              <p>RAG Queries</p>
            </div>
            <div className="stat-card">
              <h3>{((stats.storage_used_bytes || 0) / (1024 * 1024)).toFixed(2)} MB</h3>
              <p>Storage Used</p>
            </div>
          </div>
        ) : null}

        <div className="features-grid">
          <Link to="/invoices" className="feature-card">
            <h3>Invoice Processing</h3>
            <p>Extract and validate invoice data with OCR</p>
          </Link>

          <Link to="/summaries" className="feature-card">
            <h3>Document Summaries</h3>
            <p>Generate AI-powered summaries of your documents</p>
          </Link>

          <Link to="/chat" className="feature-card">
            <h3>Chat with PDF</h3>
            <p>Ask questions about your documents using RAG</p>
          </Link>

          <Link to="/filling" className="feature-card">
            <h3>Document Filling</h3>
            <p>Auto-fill PDF forms from ID documents</p>
          </Link>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
