import React from 'react';

const QuestionMultiple = ({ question, updateAnswer }) => {
  return (
    <>
      <h5>{question.data.question}</h5>
      {question.data.options.map((option, index) => (
        <div className='form-check my-1' key={index}>
          <input
            className='form-check-input'
            type="radio"
            id={option}
            name={question.title}
            onChange={(e) => updateAnswer(option)}
          />
          <label className='form-check-label' htmlFor={option}>{option}</label>
        </div>
      ))}
    </>
  );
};

export default QuestionMultiple;
