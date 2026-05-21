import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function GoogleCallback() {
  const { googleLogin } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("code");
    if (!code) { navigate("/login", { replace: true }); return; }

    googleLogin(code)
      .then(() => navigate("/dashboard", { replace: true }))
      .catch((err) =>
        navigate("/login?error=" + encodeURIComponent(getApiErrorMessage(err, "Google sign-in failed")), { replace: true })
      );
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#F4F7FF", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 40, height: 40, border: "3px solid #e2e8f0", borderTop: "3px solid #131313", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
