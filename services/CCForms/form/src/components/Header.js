import React from 'react';
import { Link } from 'react-router-dom';

const Header = ({ user, API }) => {
  const loggedView = (
    <>
      <li className='nav-item'>
        <Link to="/new" className='nav-link'>New form</Link>
      </li>
      <li className='nav-item'>
        <Link to="/list" className='nav-link'>My forms</Link>
      </li>
      <li className='nav-item'>
        <Link to="/" onClick={() => API.logout()} className='nav-link'>Logout</Link>
      </li>
    </>
  );

  const guestView = (
    <>
      <li className='nav-item'>
        <Link to="/login" className='nav-link'>Login</Link>
      </li>
      <li className='nav-item'>
        <Link to="/register" className='nav-link'>Register</Link>
      </li>
    </>
  );

  return (
    <div className="text-center navbar navbar-expand-lg navbar-light bg-light">
      <div className="container-fluid">
        <Link to="/" className='navbar-brand'>CCForms</Link>
        <ul className='navbar-nav me-auto mb-2 mb-lg-0'>
          {user ? loggedView : guestView}
        </ul>
        <span className='navbar-text'>
          {user ? `Logged in as ${user.username}` : 'Not logged in'}
        </span>
      </div>
    </div>
  );
};

export default Header;
