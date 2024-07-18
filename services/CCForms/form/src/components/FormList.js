import React from 'react';
import { Link } from 'react-router-dom';

const FormList = ({ API }) => {
  const [forms, setForms] = React.useState([]);

  React.useEffect(() => {
    API.getForms().then(setForms);
  }, [API]);

  return (
    <div>
      <h1>Form List</h1>
      {forms.length === 0 && <p>No forms available</p>}
      <ul className="list-group">
        {forms.map((form, index) => (
          <li key={index} className="list-group-item">
            <Link to={`/form/${form.id}`}>{form.title}</Link> - 
            <Link to={`/answers/${form.id}`}>show answers</Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FormList;
