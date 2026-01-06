import { Outlet, Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/auth';

export function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            NetNynja Enterprise
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Unified Network Management Platform
          </p>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
