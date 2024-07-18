import express from 'express';
import cors from 'cors';
import fs from 'fs';

import HttpError from './http-error.mjs';
import { authRouter, requireLoginMid, setLogingMid, dbConnect as dbConnectAuth } from './routes/auth.mjs';
import { formRouter, dbConnect as dbConnectForm } from './routes/form.mjs';

fs.mkdirSync(`forms`, {
  recursive: true
});

const port = 3001;
const app = express();

app.use(express.json());
app.use(cors());

app.use('/', authRouter);

app.use(setLogingMid);

app.get('/', (_req, res) => {
  res.send('Hello, world!');
});

app.use('/', formRouter);

// Catch errors
app.use((error, _req, res, _next) => {
  console.error(error);
  if (error instanceof HttpError) {
    res.status(error.code);
    res.json({ err: error.message });
  } else {
    res.status(500);
    res.json({
      message: error.message,
      stack: error.stack,
      env: process.env
    });
  }
});

await dbConnectAuth();
await dbConnectForm();
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
