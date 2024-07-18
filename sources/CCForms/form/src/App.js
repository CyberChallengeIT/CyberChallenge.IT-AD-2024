import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import './App.css';

import 'bootstrap/dist/css/bootstrap.min.css'; // Import Bootstrap CSS

// Import your API here
import useApi from './Api';

// Import your components here
import Header from './components/Header';
import Home from './components/Home';
import NewForm from './components/NewForm';
import FormList from './components/FormList';
import Form from './components/Form';
import Login from './components/Login';
import Register from './components/Register';
import Answers from './components/Answers';

function App() {
  const { user, API } = useApi();
  const [error, setError] = useState('');

  return (
    <Router>
      <Header user={user} API={API} />
      <div className="container text-center col-lg-6 mt-3">
        {error && <div className="alert alert-danger my-3">{error}</div>}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login API={API} setError={setError} />} />
          <Route path="/register" element={<Register API={API} setError={setError} />} />
          <Route path="/new" element={<NewForm API={API} setError={setError}/>} />
          <Route path="/list" element={<FormList API={API} />} />
          <Route path="/form/:formId" element={<Form API={API} setError={setError} />} />
          <Route path="/answers/:formId" element={<Answers API={API} setError={setError} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
