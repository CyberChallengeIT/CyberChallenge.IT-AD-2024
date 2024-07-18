import React from 'react';

const QuestionFile = ({ question, updateAnswer }) => {
  const handleFileChange = (e) => {
    const file = e.target.files[0];

    const reader = new FileReader();
    reader.onload = (event) => {
      // file content in base64
      const content = event.target.result.split('base64,')[1];
      const name = file.name;
      updateAnswer({ name, content });
    };
    reader.readAsDataURL(file);

  };
  return (
    <>
      <h5>{question.data.question}</h5>
      <input className='form-control' type="file" onChange={handleFileChange} />
    </>

  );
};

export default QuestionFile;
