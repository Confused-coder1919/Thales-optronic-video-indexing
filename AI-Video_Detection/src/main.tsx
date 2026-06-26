import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";
import AttributionPage from "./pages/AttributionPage";
import HomePage from "./pages/HomePage";
import LearnPage from "./pages/LearnPage";
import NotFoundPage from "./pages/NotFoundPage";
import ReviewPage from "./pages/ReviewPage";
import TestPage from "./pages/TestPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "learn", element: <LearnPage /> },
      { path: "test", element: <TestPage /> },
      { path: "review", element: <ReviewPage /> },
      { path: "attribution", element: <AttributionPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
