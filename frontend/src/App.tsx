import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import Explore from './routes/Explore';
import Catalog from './routes/Catalog';
import NewAreaToast from './components/NewAreaToast';

export default function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <strong className="brand">LiDAR Review</strong>
        <nav>
          <NavLink to="/explore">Explore</NavLink>
          <NavLink to="/catalog">Catalog</NavLink>
        </nav>
        {import.meta.env.VITE_MOCK === '1' && <span className="badge badge-warn">mock data</span>}
      </header>
      <div className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/explore" replace />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="*" element={<Navigate to="/explore" replace />} />
        </Routes>
      </div>
      <NewAreaToast />
      <footer className="attribution">
        LiDAR: GUGiK (Geoportal.gov.pl) · © OpenStreetMap contributors
      </footer>
    </div>
  );
}
