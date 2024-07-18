import React from 'react';

const NewElementEmbedded = ({ setData, API }) => {
  const [forms, setForms] = React.useState([]);

  const handleChange = (e) => {
    setData({ id: e.target.value });
  };

  React.useEffect(() => {
    API.getForms().then((f) =>{
      setForms(f);

      if (f.length > 0)
        setData({ id: f[0].id });
  });
  }, [API, setData]);

  return (
    <div>
      <label>
        Choose the form to embed
        <select className='form-select my-2' onChange={handleChange}>
          {forms.map((form, index) => (
            <option key={index} value={form.id}>
              {form.title}
            </option>
          ))
          }
        </select>

      </label>
    </div>
  );
};

export default NewElementEmbedded;
