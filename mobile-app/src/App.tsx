import { BrowserRouter, Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import HomePage from './screens/HomePage';
import BookingPage from './screens/BookingPage';
import TimelinePage from './screens/TimelinePage';
import HistoryPage from './screens/HistoryPage';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100dvh' }}>
        <main style={{ flex: 1, overflowY: 'auto' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/book" element={<BookingPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}
