import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div>
      <h5>
        Thank you for visiting our form builder!
        </h5>
      <p><Link to="/register">Register</Link> or <Link to="/login">login</Link> and use our service for free</p>
    </div>
  );
};

export default Home;
