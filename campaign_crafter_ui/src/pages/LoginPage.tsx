import React, { useState } from 'react';
import './LoginPage.css'; // Import CSS
import LoginForm from '../components/auth/LoginForm';
import { useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext'; // Assuming an AuthContext will be created later
import apiClient from '../services/apiClient'; // Or a dedicated authService
import { AxiosError } from 'axios';
import { loginUser } from '../services/userService'; // Or authService

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  // const { login } = useAuth(); // Placeholder for AuthContext
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (username_or_email: string, password: string) => {
    setError(null);
    try {
      const tokenData = await loginUser(username_or_email, password);

      localStorage.setItem('token', tokenData.access_token);
      // Update apiClient defaults AFTER successful login & token storage
      if (apiClient.defaults.headers) {
           apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
      } else {
           apiClient.defaults.headers = { common: {'Authorization': `Bearer ${tokenData.access_token}`} };
      }

      // TODO: Fetch user details and set them in AuthContext
      // const userResponse = await apiClient.get('/users/me'); // Assuming a /users/me endpoint
      // login(userResponse.data, tokenData.access_token);

      navigate('/'); // Redirect to dashboard or home page
    } catch (err) {
      const axiosError = err as AxiosError<any>;
      if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
        setError(axiosError.response.data.detail);
      } else if (axiosError.message) {
        setError(axiosError.message);
      }
      else {
        setError('Login failed. Please try again.');
      }
      console.error("Login error:", err);
    }
  };

  return (
    <div>
      <h2>Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <LoginForm onSubmit={handleLogin} />
    </div>
  );
};

export default LoginPage;
