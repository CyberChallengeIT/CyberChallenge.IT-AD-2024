import React from 'react';

const NewElement = ({ setData, data }) => {
  
  React.useEffect(() => {
    setData({ question: '' });
  }, [setData]);

  const handleQuestionChange = (e) => {
    setData({ question: e.target.value });
  };

  const question = data.question;

  return (
    <div>
      <label>
        Question
      </label>
      <input className='form-control' type="text" name="question" placeholder="Upload your document" value={question} onChange={handleQuestionChange} />
    </div>
  );
};

export default NewElement;
