import React from 'react';

import FormEmbedded from './FormEmbedded';

const QuestionEmbedded = ({ question, updateAnswer, API }) => {
  return (
    <div className="my-3 border">
      <FormEmbedded id={question.data.id} updateAnswer={updateAnswer} API={API}/>
    </div>
  );
};

export default QuestionEmbedded;
