import { useState, lazy, Suspense, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import ErrorBoundary from './components/ErrorBoundary';
import { useAuth } from './hooks/useAuth';
import LoginPage from './components/LoginPage';
import Layout, { type TabId } from './components/Layout';

// Lazy-loaded pages — only loaded when the user navigates to them
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const IndicesPage = lazy(() => import('./pages/IndicesPage'));
const ReportPage = lazy(() => import('./pages/ReportPage'));
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'));
const DataBrowserPage = lazy(() => import('./pages/DataBrowserPage'));
const RankingsPage = lazy(() => import('./pages/RankingsPage'));
const SimilarityPage = lazy(() => import('./pages/SimilarityPage'));
const PredictionPage = lazy(() => import('./pages/PredictionPage'));
const ClustersPage = lazy(() => import('./pages/ClustersPage'));
const AnalysesPage = lazy(() => import('./pages/AnalysesPage'));
const SkillCornerPage = lazy(() => import('./pages/SkillCornerPage'));
const TrajectoryPage = lazy(() => import('./pages/TrajectoryPage'));
const OpportunitiesPage = lazy(() => import('./pages/OpportunitiesPage'));
const ReplacementsPage = lazy(() => import('./pages/ReplacementsPage'));
const ContractImpactPage = lazy(() => import('./pages/ContractImpactPage'));
const ScoutingReportPage = lazy(() => import('./pages/ScoutingReportPage'));
const ApiFootballPage = lazy(() => import('./pages/ApiFootballPage'));
const CoachesPage = lazy(() => import('./pages/CoachesPage'));
const VAEPPage = lazy(() => import('./pages/VAEPPage'));

const PAGE_MAP: Record<TabId, React.LazyExoticComponent<React.ComponentType>> = {
  dashboard: DashboardPage,
  indices: IndicesPage,
  report: ReportPage,
  comparison: ComparisonPage,
  skillcorner: SkillCornerPage,
  data: DataBrowserPage,
  rankings: RankingsPage,
  similarity: SimilarityPage,
  prediction: PredictionPage,
  clusters: ClustersPage,
  analyses: AnalysesPage,
  trajectory: TrajectoryPage,
  opportunities: OpportunitiesPage,
  replacements: ReplacementsPage,
  contract_impact: ContractImpactPage,
  scouting_report: ScoutingReportPage,
  apifootball: ApiFootballPage,
  coaches: CoachesPage,
  vaep: VAEPPage,
};

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
    </div>
  );
}

function getInitialTab(): TabId {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get('tab');
  if (tab && tab in PAGE_MAP) return tab as TabId;
  return 'dashboard';
}

function App() {
  const { user, isAuthenticated, loading, error, login, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>(getInitialTab);

  // Clean URL params after reading (keep clean URL)
  useEffect(() => {
    if (window.location.search && !window.location.search.includes('player=')) {
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  if (!isAuthenticated || !user) {
    return <LoginPage onLogin={login} loading={loading} error={error} />;
  }

  const PageComponent = PAGE_MAP[activeTab] || DashboardPage;

  return (
    <ErrorBoundary>
      <Layout user={user} activeTab={activeTab} onTabChange={setActiveTab} onLogout={logout}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            <ErrorBoundary>
              <Suspense fallback={<PageLoader />}>
                <PageComponent />
              </Suspense>
            </ErrorBoundary>
          </motion.div>
        </AnimatePresence>
      </Layout>
      <Analytics />
      <SpeedInsights />
    </ErrorBoundary>
  );
}

export default App;
