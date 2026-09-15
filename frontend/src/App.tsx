import { NavLink, Route, Routes } from "react-router-dom";
import JobDescriptionsPage from "./pages/JobDescriptionsPage";
import ResumeUploadPage from "./pages/ResumeUploadPage";
import RunPage from "./pages/RunPage";
import RunResultsPage from "./pages/RunResultsPage";
import RunHistoryPage from "./pages/RunHistoryPage";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Resume Screening</h1>
        <nav>
          <NavLink to="/" end>
            Job Descriptions
          </NavLink>
          <NavLink to="/resumes">Resumes</NavLink>
          <NavLink to="/run">New Run</NavLink>
          <NavLink to="/history">Run History</NavLink>
        </nav>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<JobDescriptionsPage />} />
          <Route path="/resumes" element={<ResumeUploadPage />} />
          <Route path="/run" element={<RunPage />} />
          <Route path="/runs/:runId" element={<RunResultsPage />} />
          <Route path="/history" element={<RunHistoryPage />} />
        </Routes>
      </main>
    </div>
  );
}
