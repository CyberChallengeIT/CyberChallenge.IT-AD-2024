import React from 'react';
import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';

import Question from './Question';

function Form({ API, setError }) {
  const [data, setData] = useState(null);
  const { formId } = useParams();
  const [message, setMessage] = useState('');

  const updateAnswer = (questionIndex, answer) => {
    setData((prevData) => {
      const newAnswers = [...prevData.answers];
      newAnswers[questionIndex] = answer;
      return { ...prevData, answers: newAnswers };
    });
  };

  const submitAnswer = () => {
    API.submitAnswer(data)
      .then((res) => {
        console.log(res);
        setMessage('Answer submitted successfully');
      })
      .catch((error) => {
        console.error('Error submitting answer:', error);
        setError(error.message);
      });
  };

  useEffect(() => {
    API.getForm(formId).then((d) => {
      d.id = formId;
      d.answers = Array(d.questions.length).fill(null);
      setData(d);
    });
  }, [API, formId]);

  if (data === null) {
    return 'Loading...';
  }

  if (message) {
    return (
      <>
        <div className="alert alert-success">{message}</div>
        <div>Thanks for submitting your answers!</div>
        <Link to="/" className="btn btn-primary my-3">
          Back to home
        </Link>
      </>
    );
  }

  return (
    <>
      <div>
        <h1>{data.title}</h1>
        {data.questions.map((question, index) => (
          <Question
            key={index}
            question={question}
            updateAnswer={(ans) => updateAnswer(index, ans)}
            API={API}
          />
        ))}
        <button className="my-3 btn btn-primary" onClick={submitAnswer}>
          Submit answer
        </button>
      </div>
    </>
  );
}
export default Form;
