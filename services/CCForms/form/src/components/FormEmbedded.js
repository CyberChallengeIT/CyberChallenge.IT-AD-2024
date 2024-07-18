import React from 'react';
import { useState, useEffect } from 'react';

import Question from './Question';

function FormEmbedded({ API, setError, id }) {
  const [data, setData] = useState(null);

  useEffect(() => {
      if (!id) {
        return;
      }
      API.getForm(id).then((d) => {
      d.id = id;
      d.answers = Array(d.questions.length).fill(null);
      setData(d);
    });
  }, [API, id]);

  if (data === null) {
    return 'Loading...';
  }



  return (
    <>
      <div>
        <h1>{data.title}</h1>
        {data.questions.map((question, index) => (
          <Question
            key={index}
            question={question}
            updateAnswer={() => {}}
          />
        ))}
      </div>
    </>
  );
}
export default FormEmbedded;
