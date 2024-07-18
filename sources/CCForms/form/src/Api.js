import { useState } from 'react';

function useApi() {
  const API_URL = window.location.origin.replace('3000', '3001');

  let u = null;
  const localUser = localStorage.getItem('user');
  if (localUser) {
    u = JSON.parse(localUser);
  }

  const [user, setUser] = useState(u);

  async function login(username, password) {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error logging in:', data);
        throw new Error(data.err);
      }

      setUser(data);
      localStorage.setItem('user', JSON.stringify(data));

      return data;
    } catch (error) {
      console.error('Error logging in:', error);
      throw error;
    }
  }

  async function register(username, password) {
    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error registering:', data);
        throw new Error(data.err);
      }

      console.log('Registered successfully:', data);

      setUser(data);
      localStorage.setItem('user', JSON.stringify(data));

      return data;
    } catch (error) {
      console.error('Error registering:', error);
      throw error;
    }
  }

  async function logout() {
    setUser(null);
    localStorage.removeItem('user');
  }

  async function saveForm(question) {
    try {
      const response = await fetch(`${API_URL}/new`, {
        method: 'POST',
        body: JSON.stringify(question),
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${user.token}`
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error saving form:', data);
        throw new Error(data.err);
      }

      console.log('Form saved successfully:', data);

      return data.id;
    } catch (error) {
      console.error('Error saving form:', error);
      throw error;
    }
  }

  async function getForm(id) {
    try {
      const response = await fetch(`${API_URL}/form/${id}`, {
        headers: {
          Authorization: `Bearer ${user.token}`
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error retrieving form:', data);
        throw new Error(data.err);
      }

      console.log('Form retrieved successfully:', data);

      return data;
    } catch (error) {
      // Handle any errors that occur during the API request
      console.error('Error retrieving form:', error);

      // Return an error status or throw an exception
      throw error;
    }
  }

  async function getForms() {
    try {
      const response = await fetch(`${API_URL}/forms`, {
        headers: {
          Authorization: `Bearer ${user.token}`
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error retrieving forms:', data);
        throw new Error(data.err);
      }

      console.log('Forms retrieved successfully:', data);

      return data;
    } catch (error) {
      // Handle any errors that occur during the API request
      console.error('Error retrieving forms:', error);

      // Return an error status or throw an exception
      throw error;
    }
  }

  async function submitAnswer(form) {
    const id = form.id;
    const answers = form.answers;
    try {
      const response = await fetch(`${API_URL}/form/${id}/answer`, {
        method: 'POST',
        body: JSON.stringify(answers),
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${user.token}`
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error submitting answer:', data);
        throw new Error(data.err);
      }

      console.log('Answer submitted successfully:', data);

      return data;
    } catch (error) {
      // Handle any errors that occur during the API request
      console.error('Error submitting answer:', error);

      // Return an error status or throw an exception
      throw error;
    }
  }

  async function getAnswers(id) {
    try {
      const response = await fetch(`${API_URL}/form/${id}/answers`, {
        headers: {
          Authorization: `Bearer ${user.token}`
        }
      });

      const data = await response.json();

      if (response.status !== 200) {
        console.error('Error retrieving answers:', data);
        throw new Error(data.err);
      }
      console.log('Answers retrieved successfully:', data);
      return data;
    } catch (error) {
      // Handle any errors that occur during the API request
      console.error('Error retrieving answers:', error);

      // Return an error status or throw an exception
      throw error;
    }
  }

  return {
    user,
    setUser,
    API: {
      login,
      register,
      logout,
      saveForm,
      getForm,
      getForms,
      submitAnswer,
      getAnswers,
      baseUrl: API_URL
    }
  };
}

export default useApi;
