import React from 'react';

const NewElement = ({ setData, data }) => {
  React.useEffect(() => { 
    setData({ question: '', options: [] })
  }, [setData])

  const handleQuestionChange = (e) => {
    setData((prevData) => ({ ...prevData, question: e.target.value }));
  };

  const handleOptionChange = (e, index) => {
    setData((prevData) => {
      const newOptions = [...prevData.options];
      newOptions[index] = e.target.value;
      return { ...prevData, options: newOptions };
    });
  };

  const handleAddOption = () => {
    setData((prevData) => ({ ...prevData, options: [...prevData.options, ''] }));
  }

  if (!data) {
    return 'Loading...';
  }

  const question = data.question;
  const options = data.options;

  if (!options) {
    return 'Loading...';
  }

  return (
    <div>
        <label>
          Question
        </label>
        <input className='form-control' type="text" name="question" value={question} onChange={handleQuestionChange} />

        {options.map((option, index) => (
          <div className='my-2' key={index}>
            Option {index + 1}
            <input
              type="text"
              className='form-control'
              name={`option${index + 1}`}
              value={option}
              onChange={(e) => handleOptionChange(e, index)}
            />
          </div>
        ))}
        <button className='btn btn-light my-2' type="button" onClick={handleAddOption}>
          Add option
        </button>
    </div>
  );
};

export default NewElement;
