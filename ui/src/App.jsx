import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage.jsx";
import RunPage from "./pages/RunPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import Layout from "./components/Layout.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/run/:executionId" element={<RunPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
    </Routes>
  );
}