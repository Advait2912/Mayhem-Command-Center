import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { NewPredict } from './pages/NewPredict';
import { LivePredict } from './pages/LivePredict';
import { Outcomes } from './pages/Outcomes';
import { Landing } from './pages/Landing';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="new" element={<NewPredict />} />
          <Route path="live" element={<LivePredict />} />
          <Route path="outcomes" element={<Outcomes />} />
          <Route path="*" element={<Navigate to="/app" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
