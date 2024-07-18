import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import NewElement from './NewElement';
import Question from './Question';

function NewForm({ API, setError }) {
  const [questions, setQuestions] = useState([]);
  const [formTitle, setFormTitle] = useState('');

  const navigate = useNavigate();

  const addQuestion = (newQuestion) => {
    setQuestions([...questions, newQuestion]);
  };

  const saveFormClick = async () => {
    console.log('saving form');

    if (!formTitle) {
      setError('Form title is required');
      return;
    }

    try {
      const form = {
        title: formTitle,
        questions
      };

      await API.saveForm(form);
      navigate('/list');
    } catch (error) {
      setError(error.message);
      console.error('Error saving form:', error);
    }
  };

  const cancelForm = () => {
    setQuestions([]);
  };

  return (
    <>
      <div className='d-flex justify-content-between'>
        <button onClick={cancelForm} className='btn btn-secondary'>Cancel</button>
        <h3>New form</h3>
        <button onClick={saveFormClick} className='btn btn-primary'>Save</button>
      </div>

      <div className='form-group my-3'>
        <input
          type="text"
          name="formTitle"
          className='form-control'
          placeholder='Form title'
          value={formTitle}
          onChange={(e) => {setError(''); setFormTitle(e.target.value)}}
        />
        <br />
      </div>


      <div>
        {questions.map((question, index) => (
          <Question key={index} question={question} API={API} updateAnswer={() => { }} />
        ))}

        <NewElement addQuestion={addQuestion} API={API} setError={setError} />
      </div>
    </>
  );
}

export default NewForm;
