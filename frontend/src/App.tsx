import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Context Providers
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './hooks/useAuth';

// Import JsonViewer demo
import JsonViewerDemo from './components/JsonViewerDemo';

// Components
import Layout from './components/Layout';
import LoadingSpinner from './components/LoadingSpinner';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Interpretations from './pages/Interpretations';
import InterpretationDetail from './pages/InterpretationDetail';
import InterpretationEditor from './pages/InterpretationEditor';
import ProductConfigAdmin from './pages/ProductConfigAdmin';

// Placeholder components for routes not yet implemented
const TemplatesPage = () => <div>Templates Page (Coming Soon)</div>;
const TemplateEditorPage = () => <div>Template Editor (Coming Soon)</div>;
const ReportsPage = () => <div>Reports Page (Coming Soon)</div>;
const ReportEditorPage = () => <div>Report Editor (Coming Soon)</div>;
const ReportViewPage = () => <div>Report View (Coming Soon)</div>;
const ProfilePage = () => <div>Profile Page (Coming Soon)</div>;
const NotFoundPage = () => <div>404 - Page Not Found</div>;

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontWeight: 600,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        },
      },
    },
  },
});

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { state } = useAuth();
  const { user, loading } = state;

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <LoadingSpinner />
      </Box>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Public Route Component (redirect to dashboard if authenticated)
interface PublicRouteProps {
  children: React.ReactNode;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { state } = useAuth();
  const { user, loading } = state;

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <LoadingSpinner />
      </Box>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// App Routes Component
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* Root redirect to dashboard */}
      <Route
        path="/"
        element={<Navigate to="/dashboard" replace />}
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* Templates */}
      <Route
        path="/templates"
        element={
          <ProtectedRoute>
            <Layout>
              <TemplatesPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/templates/new"
        element={
          <ProtectedRoute>
            <Layout>
              <TemplateEditorPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/templates/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <TemplateEditorPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* Reports */}
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <Layout>
              <ReportsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports/new"
        element={
          <ProtectedRoute>
            <Layout>
              <ReportEditorPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports/:id/edit"
        element={
          <ProtectedRoute>
            <Layout>
              <ReportEditorPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <ReportViewPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* Interpretations */}
      <Route
        path="/interpretations"
        element={
          <ProtectedRoute>
            <Layout>
              <Interpretations />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interpretations/new"
        element={
          <ProtectedRoute>
            <Layout>
              <InterpretationEditor mode="create" />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interpretations/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <InterpretationDetail />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interpretations/:id/edit"
        element={
          <ProtectedRoute>
            <Layout>
              <InterpretationEditor mode="edit" />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* Product Configurations */}
      <Route
        path="/admin/product-configs"
        element={
          <ProtectedRoute>
            <Layout>
              <ProductConfigAdmin />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* Profile */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Layout>
              <ProfilePage />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* JsonViewer Demo */}
      <Route
        path="/json-demo"
        element={
          <ProtectedRoute>
            <Layout>
              <JsonViewerDemo />
            </Layout>
          </ProtectedRoute>
        }
      />
      
      {/* 404 - Must be last */}
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <Layout>
              <NotFoundPage />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

// Main App Component
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <AppRoutes />
          </Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4caf50',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#f44336',
                  secondary: '#fff',
                },
              },
            }}
          />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;