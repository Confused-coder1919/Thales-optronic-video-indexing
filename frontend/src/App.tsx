import { Route, Routes, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Home from "./pages/Home";
import VideosLibrary from "./pages/VideosLibrary";
import Upload from "./pages/Upload";
import VideoDetails from "./pages/VideoDetails";
import Search from "./pages/Search";
import ShareReport from "./pages/ShareReport";

export default function App() {
  const location = useLocation();
  const isShare = location.pathname.startsWith("/share/");

  return (
    <div className="min-h-screen bg-ei-bg">
      <TopBar />
      <div className="flex min-h-[calc(100vh-56px)]">
        {!isShare && <Sidebar />}
        <main className="flex-1 px-8 py-6">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/videos" element={<VideosLibrary />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/videos/:id" element={<VideoDetails />} />
            <Route path="/search" element={<Search />} />
            <Route path="/share/:token" element={<ShareReport />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
