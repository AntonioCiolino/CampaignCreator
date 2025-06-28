import React, { useState } from 'react';
import './LoginForm.css'; // Import CSS

interface LoginFormProps {
  onSubmit: (username_or_email: string, password: string) => void;
  // error?: string | null; // Optional: Pass error message to display in form
}

const LoginForm: React.FC<LoginFormProps> = ({ onSubmit }) => {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSubmit(usernameOrEmail, password);
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <div>
        <label htmlFor="usernameOrEmail">Username or Email:</label>
        <input
          type="text"
          id="usernameOrEmail"
          value={usernameOrEmail}
          onChange={(e) => setUsernameOrEmail(e.target.value)}
          required
          autoComplete="username"
        />
      </div>
      <div>
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </div>
      <button type="submit">Login</button>
    </form>
  );
};

export default LoginForm;
