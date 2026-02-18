import { Outlet, Navigate } from "react-router-dom";
import { useAuthStore } from "../../stores/auth";

export function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-900">
      {/* Professional dark cyberpunk background */}
      <div
        className="absolute inset-0"
        style={{ backgroundColor: "#080c14" }}
      />
      {/* Circuit grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      {/* Diagonal depth lines */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(135deg, rgba(0,212,255,0.05) 25%, transparent 25%, transparent 50%, rgba(0,212,255,0.05) 50%, rgba(0,212,255,0.05) 75%, transparent 75%)",
          backgroundSize: "80px 80px",
        }}
      />
      {/* Cyan glow — top centre */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,212,255,0.10) 0%, transparent 70%)",
        }}
      />
      {/* Magenta glow — bottom centre */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 60% 40% at 50% 110%, rgba(217,70,239,0.08) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 w-full max-w-md p-8">
        <Outlet />
      </div>
    </div>
  );
}
