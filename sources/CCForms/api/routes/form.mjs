import express from 'express';
import { Sequelize, DataTypes, Op } from 'sequelize';
import { v4 as uuid } from 'uuid';
import fs from 'fs';

import asyncWrapper from '../express-async-wrapper.mjs';
import HttpError from '../http-error.mjs';
import {requireLoginMid} from './auth.mjs';

const router = express.Router();

const sequelize = new Sequelize({
  host: 'postgres',
  database: 'forms',
  username: 'formsuser',
  password: 'formspass',
  dialect: 'postgres',
  pool: {
    max: 5,
    min: 1,
    idle: 10000
  },
  logging: false,
  define: {
    timestamps: false
  }
});

const Form = sequelize.define('Form', {
  id: {
    type: DataTypes.UUID,
    defaultValue: Sequelize.UUIDV4,
    primaryKey: true
  },
  title: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  owner_id: {
    type: DataTypes.UUID,
    allowNull: false
  }
});

const Answers = sequelize.define('Answers', {
  id: {
    type: DataTypes.UUID,
    defaultValue: Sequelize.UUIDV4,
    primaryKey: true
  },
  answer: {
    type: DataTypes.STRING(5000),
    allowNull: false
  },
  user_id: {
    type: DataTypes.UUID,
    allowNull: false
  }
});

const Files = sequelize.define('Files', {
  id: {
    type: DataTypes.UUID,
    defaultValue: Sequelize.UUIDV4,
    primaryKey: true
  },
  name: {
    type: DataTypes.STRING(255),
    allowNull: false
  },
  content: {
    type: DataTypes.BLOB(5000),
    allowNull: false
  }
});

Form.beforeCreate((form) => {
  form.id = uuid();
});

Answers.beforeCreate((answer) => {
  answer.id = uuid();
});

Form.hasMany(Answers);
Answers.belongsTo(Form);

const dbConnect = async () => {
  try {
    await sequelize.authenticate();
    await sequelize.sync();

    return true;
  } catch (error) {
    console.log('DB', error);

    console.log('DB sync (connection) failed, retrying in 10 seconds');
    await new Promise((resolve) => setTimeout(resolve, 10000));
    return await dbConnect();
  }
};


router.get('/file/:id', asyncWrapper(async (req, res) => {
  const id = req.params.id;

  if (!id || id.length !== 36) {
    throw new HttpError(400, 'Invalid file ID');
  }

  try {
    const file = await Files.findOne({ where: { id } });
    if (file === null) {
      throw new HttpError(404, 'File not found');
    }

    res.setHeader('Content-Disposition', `attachment; filename="${file.name}"`);
    res.setHeader('Content-Type', 'application/octet-stream');
    res.send(file.content);

  } catch (err) {
    console.error(err);
    throw new HttpError(500, 'Failed to retrieve file');
  }
})
);

router.use(requireLoginMid);


router.post('/new', async (req, res) => {
  const form = req.body;

  if (!form.title || !form.questions) {
    res.status(400).json({ err: 'Invalid form' });
    return;
  }

  const owner_id = req.user.id;

  try {
    const newForm = await Form.create({ title: form.title, owner_id });

    fs.writeFileSync(`forms/${newForm.id}.json`, JSON.stringify(form.questions));
    res.json({ id: newForm.id });
  } catch (err) {
    console.error(err);
    res.status(500).json({ err: 'Failed to create form' });
  }
});

router.get('/forms', async (req, res) => {
  const owner_id = req.user.id;

  try {
    const forms = await Form.findAll({ where: { owner_id } });
    res.json(forms.map((form) => ({ id: form.id, title: form.title })));
  } catch (err) {
    console.error(err);
    res.status(500).json({ err: 'Failed to retrieve forms' });
  }
});

router.get(
  '/form/:id',
  asyncWrapper(async (req, res) => {
    const id = req.params.id;

    if (!id || id.length !== 36) {
      throw new HttpError(400, 'Invalid form ID');
    }

    const form = await Form.findOne({ where: { id } });
    if (form === null) {
      throw new HttpError(404, 'Form not found');
    }

    const question = JSON.parse(fs.readFileSync(`forms/${id}.json`));
    const newQuestions = [];

    // Add embedded questions (this feature is not used by the web client, but only by the API clients)
    for (const q of question) {
      if (q.type === 'embedded') {
        if (q.data.id && /^[a-f0-9-]{36}$/.test(q.data.id)){
          const embeddedQuestions = JSON.parse(fs.readFileSync(`forms/${q.data.id}.json`));
          for (const e of embeddedQuestions) {
            newQuestions.push(e);
          }
        }
      } else {
        newQuestions.push(q);
      }
    }

    if (form.owner_id !== req.user.id) {
      for (const newQuestion of newQuestions) {
        delete newQuestion.note;
      }
    }

    res.json({ id: form.id, title: form.title, questions: newQuestions });
  })
);

router.post(
  '/form/:id/answer',
  asyncWrapper(async (req, res) => {
    const id = req.params.id;
    const userAnswer = req.body;

    if (!id || id.length !== 36 || !userAnswer) {
      throw new HttpError(400, 'Invalid answer');
    }

    const form = await Form.findByPk(id);

    if (form === null) {
      throw new HttpError(404, 'Form not found');
    }

    const questionsOld = JSON.parse(fs.readFileSync(`forms/${id}.json`));

    const questions = [];

    // Add embedded questions (this feature is not used by the web client, but only by the API clients)
    for (const q of questionsOld) {
      if (q.type === 'embedded') {
        const embeddedQuestions = JSON.parse(fs.readFileSync(`forms/${q.data.id}.json`));
        for (const e of embeddedQuestions) {
          questions.push(e);
        }
      } else {
        questions.push(q);
      }
    }

    if (questions.length !== userAnswer.length) {
      throw new HttpError(400, 'Invalid answer');
    }

    const files = []
    for (let i=0 ; i<questions.length ; i++) {
      const answer = userAnswer[i];
      if (questions[i].type === 'file') {
        if ((answer.content || '').length > 5000) {
          throw new HttpError(400, 'File content too long');
        }
        const fid = uuid();
        files.push({id: fid, name: answer.name, content: answer.content});
        delete answer.content;
        answer.file_id = fid;
      }
    }

    try {
      const answer = await Answers.create({
        form_id: id,
        answer: JSON.stringify(userAnswer),
        user_id: req.user.id
      });

      await form.addAnswers(answer);

      for (const file of files) {
        await Files.create({
          id: file.id,
          name: file.name,
          content: sequelize.literal(`decode('${file.content}', 'base64')`)
        });
      }

      res.json({ id: answer.id });
    } catch (err) {
      console.error(err);
      throw new HttpError(500, 'Failed to submit answer');
    }
  })
);

router.get(
  '/form/:id/answers',
  asyncWrapper(async (req, res) => {
    const id = req.params.id;

    if (!id || id.length !== 36) {
      throw new HttpError(400, 'Invalid form ID');
    }
    const form_id = id;

    try {
      const form = await Form.findByPk(form_id, {
        include: Answers
      });

      res.json(
        form.Answers.map((answer) => ({
          id: answer.id,
          answer: JSON.parse(answer.answer),
          user_id: answer.user_id
        }))
      );
    } catch (err) {
      console.error(err);
      throw new HttpError(500, 'Failed to retrieve answers');
    }
  })
);

export { router as formRouter, dbConnect };
