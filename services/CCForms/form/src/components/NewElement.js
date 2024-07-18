import React, { useState } from 'react';
import NewElementMultiple from './NewElementMultiple';
import NewElementText from './NewElementText';
import NewElementFile from './NewElementFile';
import NewElementEmbedded from './NewElementEmbedded';

const NewElement = ({ addQuestion, API, setError }) => {
  const [type, setType] = useState('multiple');
  const [title, setTitle] = useState('');
  const [data, setData] = useState(null);
  const [note, setNote] = useState('');

  const addQuestionGeneric = () => {
    if (!title) {
      setError('Question title is required');
      return;
    }

    const question = {
      title,
      type,
      data,
      note
    };
    addQuestion(question);
    setTitle('');
  };

  const handleTitleChange = (e) => {
    setError('');
    setTitle(e.target.value);
  };

  return (
    <div className='card my-3'>
      <div className='card-header'>
        <h5>New question</h5>
        <div className='row'>
          <input className='form-control col mx-3' type="text" name="title" placeholder='Question title' value={title} onChange={handleTitleChange} />
          <select className='form-select col mx-3' value={type} onChange={(e) => setType(e.target.value)}>
            <option value="multiple">Multiple Choice</option>
            <option value="text">Text</option>
            <option value="file">File</option>
            <option value="embedded">Embedded</option>
          </select>
        </div>
      </div>
      <div className='card-body'>

        {type === 'multiple' && <NewElementMultiple data={data} setData={setData} />}
        {type === 'text' && <NewElementText data={data} setData={setData} />}
        {type === 'file' && <NewElementFile data={data} setData={setData} />}
        {type === 'embedded' && <NewElementEmbedded API={API} data={data} setData={setData} />}
      </div>
      <div className='card-footer'>
        <div className='row'>
          <div className='col'>
            <input className='form-control' type="text" name="note" placeholder='Note (private)' onChange={(e) => setNote(e.target.value) }/>
          </div>
          <div className='col text-end'>
            <button className='btn btn-light' onClick={() => addQuestionGeneric()}>Add question</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewElement;
