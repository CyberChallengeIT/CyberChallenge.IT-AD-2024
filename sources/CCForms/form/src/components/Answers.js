import React from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

function Answers({ API, setError }) {
  const { formId } = useParams();
  const [answers, setAnswers] = useState([]);
  const [form, setForm] = useState(null);

  useEffect(() => {
    API.getForm(formId)
      .then(setForm)
      .catch((error) => {
        console.error('Error getting form:', error);
        setError(error.message);
      });

    API.getAnswers(formId).then(setAnswers);
  }, [API, formId, setError]);

  if (form === null) {
    return 'Loading...';
  }

  
  const recapAnswers = Array(form.questions.length);
  for (let i = 0; i < recapAnswers.length; i++) {
    recapAnswers[i] = [];
  }

  for (const ans of answers) {
    console.log('Answer : ', ans);
    for (let i = 0; i < recapAnswers.length; i++) {
      if (ans.answer[i])
        recapAnswers[i].push(ans.answer[i]);
    }
  }
  console.log(recapAnswers);
  return (
    <div>
      <h1>Answers</h1>
      {recapAnswers.map((answers, i) => (
        <div key={i} className="card my-3">
          <div className="card-header">{form.questions[i].title}</div>
          <div className="card-body">
            <ul>
              {answers.map((answer, j) => {
                if (form.questions[i].type === 'file') {
                  return (
                    <li key={j}>
                      <a href={`${API.baseUrl}/file/${answer.file_id}`} download={answer.name}>
                        {answer.name}
                      </a>
                    </li>
                  );
                } 
                return <li key={j}>{answer}</li>;
              })
              }
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
  

}
export default Answers;
