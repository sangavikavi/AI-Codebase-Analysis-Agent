import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import AuthModal from './components/AuthModal';
import ProjectsDashboard from './pages/ProjectsDashboard';
import CreateProject from './pages/CreateProject';
import LiveAnalysis from './pages/LiveAnalysis';
import DocumentationView from './pages/DocumentationView';
import CodebaseQA from './pages/CodebaseQA';
import AdminDashboard from './pages/AdminDashboard';
import { getAuthToken, getUserInfo, api } from './api/client';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!getAuthToken());
  const [activeTab, setActiveTab] = useState('projects');
  const [activeProject, setActiveProject] = useState(null);

  useEffect(() => {
    // If authenticated, check if there are projects and set first one as active
    if (isAuthenticated) {
      api.listProjects()
        .then((projs) => {
          if (projs && projs.length > 0 && !activeProject) {
            setActiveProject(projs[0]);
          }
        })
        .catch(() => {});
    }
  }, [isAuthenticated]);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setActiveTab('projects');
  };

  const handleLogout = () => {
    api.logout();
    setIsAuthenticated(false);
    setActiveProject(null);
  };

  const handleSelectProject = (project) => {
    setActiveProject(project);
    setActiveTab('analysis');
  };

  const handleProjectCreated = (project) => {
    setActiveProject(project);
    setActiveTab('analysis');
  };

  if (!isAuthenticated) {
    return <AuthModal onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
      <Navbar activeProject={activeProject} onLogout={handleLogout} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        <main className="flex-1 overflow-y-auto bg-[#0a0f1d]/50">
          {activeTab === 'projects' && (
            <ProjectsDashboard
              onSelectProject={handleSelectProject}
              onNavigateToCreate={() => setActiveTab('create')}
            />
          )}

          {activeTab === 'create' && (
            <CreateProject onProjectCreated={handleProjectCreated} />
          )}

          {activeTab === 'analysis' && (
            <LiveAnalysis
              activeProject={activeProject}
              onGoToReports={() => setActiveTab('docs')}
            />
          )}

          {activeTab === 'docs' && (
            <DocumentationView activeProject={activeProject} />
          )}

          {activeTab === 'qa' && (
            <CodebaseQA activeProject={activeProject} />
          )}

          {activeTab === 'admin' && (
            <AdminDashboard />
          )}
        </main>
      </div>
    </div>
  );
}
