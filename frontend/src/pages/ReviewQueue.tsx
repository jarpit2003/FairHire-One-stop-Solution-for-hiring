import { Navigate } from "react-router-dom";

// Legacy page — superseded by Pipeline page
export default function ReviewQueue() {
  return <Navigate to="/pipeline" replace />;
}
