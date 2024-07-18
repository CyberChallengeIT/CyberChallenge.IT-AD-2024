import React from 'react';

import QuestionMultiple from './QuestionMultiple';
import QuestionText from './QuestionText';
import QuestionFile from './QuestionFile';
import QuestionEmbedded from './QuestionEmbedded';

const Question = ({ question, updateAnswer, API }) => {
  let q = <></>;

  switch (question.type) {
    case 'multiple':
      q = <QuestionMultiple question={question} updateAnswer={updateAnswer} />;
      break;
    case 'text':
      q = <QuestionText question={question} updateAnswer={updateAnswer} />;
      break;
    case 'file':
      q = <QuestionFile question={question} updateAnswer={updateAnswer} />;
      break;
    case 'embedded':
      q = <QuestionEmbedded question={question} updateAnswer={updateAnswer} API={API} />;
      break
    default:
      q = <h4>Invalid type?!</h4>;
  }

  return <div className='card my-3'>
    <div className='card-header'>{question.title} - {question.type}</div>
    <div className='card-body'>
      {q}
    </div>
    {question.note && <div className='card-footer'>{question.note}</div>}
  </div>
};

export default Question;
