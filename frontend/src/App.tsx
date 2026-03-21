import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import { useAuth } from './hooks/useAuth';
import LoginPage from './components/LoginPage';
import Layout, { type TabId } from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import IndicesPage from './pages/IndicesPage';
import ReportPage from './pages/ReportPage';
import ComparisonPage from './pages/ComparisonPage';
import DataBrowserPage from './pages/DataBrowserPage';
import RankingsPage from './pages/RankingsPage';
import SimilarityPage from './pages/SimilarityPage';
import PredictionPage from './pages/PredictionPage';
import ClustersPage from './pages/ClustersPage';
import AnalysesPage from './pages/AnalysesPage';
import SkillCornerPage from './pages/SkillCornerPage';
import TrajectoryPage from './pages/TrajectoryPage';
import OpportunitiesPage from './pages/OpportunitiesPage';
import ReplacementsPage from './pages/ReplacementsPage';
import ContractImpactPage from './pages/ContractImpactPage';
import ScoutingReportPage from './pages/ScoutingReportPage';

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
      case 'indices':
        return <IndicesPage />;
      case 'report':
        return <ReportPage />;
      case 'comparison':
        return <ComparisonPage />;
      case 'skillcorner':
        return <SkillCornerPage />;
      case 'data':
        return <DataBrowserPage />;
      case 'rankings':
        return <RankingsPage />;
      case 'similarity':
        return <SimilarityPage />;
      case 'prediction':
        return <PredictionPage />;
      case 'clusters':
        return <ClustersPage />;
      case 'analyses':
        return <AnalysesPage />;
      case 'trajectory':
        return <TrajectoryPage />;
      case 'opportunities':
        return <OpportunitiesPage />;
      case 'replacements':
        return <ReplacementsPage />;
      case 'contract_impact':
        return <ContractImpactPage />;
      case 'scouting_report':
        return <ScoutingReportPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <>
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
      </Layout>
      <Analytics />
      <SpeedInsights />
    </>
  );
}

export default App;
