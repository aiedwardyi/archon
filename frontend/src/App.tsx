import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Index from "./pages/Index";
import PipelineRun from "./pages/PipelineRun";
import VersionHistory from "./pages/VersionHistory";
import ArtifactViewer from "./pages/ArtifactViewer";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/pipeline" element={<PipelineRun />} />
          <Route path="/versions" element={<VersionHistory />} />
          <Route path="/artifacts" element={<ArtifactViewer />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
