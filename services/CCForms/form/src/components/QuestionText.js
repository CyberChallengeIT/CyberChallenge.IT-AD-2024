import React from 'react';

const QuestionText = ({ question, updateAnswer }) => {
  return (
    <>
      <h5>{question.data.question}</h5>
      <input className='form-control' type="text" onChange={(e) => updateAnswer(e.target.value)} />
    </>
  );
};

export default QuestionText;
