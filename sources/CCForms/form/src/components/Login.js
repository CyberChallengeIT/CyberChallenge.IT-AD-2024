import React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = ({ API, setError }) => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    try {
      await API.login(username, password);

      navigate('/');
    } catch (error) {
      console.error('Error logging in:', error);
      setError(error.message);
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form>
        <div className="form-group my-3">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            className="form-control"
            id="username"
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="form-group my-3">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            className="form-control"
            id="password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary my-3" onClick={handleSubmit}>
          Login
        </button>
      </form>
    </div>
  );
};

export default Login;
