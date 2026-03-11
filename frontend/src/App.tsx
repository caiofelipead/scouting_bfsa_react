import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { SpeedInsights } from '@vercel/speed-insights/react';
import { useAuth } from './hooks/useAuth';
import LoginPage from './components/LoginPage';
import Layout, { type TabId } from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import RankingsPage from './pages/RankingsPage';
import SimilarityPage from './pages/SimilarityPage';
import OfferedPage from './pages/OfferedPage';
import AnalysesPage from './pages/AnalysesPage';

function App() {
  const { user, isAuthenticated, loading, error, login, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  if (!isAuthenticated || !user) {
    return <LoginPage onLogin={login} loading={loading} error={error} />;
  }

  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'rankings':
        return <RankingsPage />;
      case 'similarity':
        return <SimilarityPage />;
      case 'offered':
        return <OfferedPage />;
      case 'analyses':
        return <AnalysesPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <Layout user={user} activeTab={activeTab} onTabChange={setActiveTab} onLogout={logout}>
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
        >
          {renderPage()}
        </motion.div>
      </AnimatePresence>
      <SpeedInsights />
    </Layout>
  );
}

export default App;
