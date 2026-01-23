import { Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";
import VideosLibrary from "./pages/VideosLibrary";
import Upload from "./pages/Upload";
import VideoDetails from "./pages/VideoDetails";
import Search from "./pages/Search";

export default function App() {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 bg-ei-bg min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/library" element={<VideosLibrary />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/videos/:id" element={<VideoDetails />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </main>
    </div>
  );
}
