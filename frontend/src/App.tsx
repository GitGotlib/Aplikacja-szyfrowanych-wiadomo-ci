import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './router/AppRoutes';
import { AuthProvider } from './auth/AuthContext';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
