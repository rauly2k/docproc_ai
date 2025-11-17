import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentFilling } from './pages/DocumentFilling';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          {/* Navigation */}
          <nav className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center">
                    <h1 className="text-xl font-bold text-primary-600">
                      Document AI
                    </h1>
                  </div>
                  <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                    <Link
                      to="/"
                      className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Dashboard
                    </Link>
                    <Link
                      to="/filling"
                      className="border-primary-500 text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    >
                      Document Filling
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route
                path="/"
                element={
                  <div>
                    <h2 className="text-2xl font-bold mb-4">Welcome to Document AI</h2>
                    <p className="text-gray-600 mb-4">
                      Intelligent document processing powered by AI.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="font-medium mb-2">Document Filling</h3>
                        <p className="text-sm text-gray-600 mb-4">
                          Extract data from ID cards and automatically fill PDF forms.
                        </p>
                        <Link
                          to="/filling"
                          className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                        >
                          Get Started →
                        </Link>
                      </div>
                    </div>
                  </div>
                }
              />
              <Route path="/filling" element={<DocumentFilling />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
