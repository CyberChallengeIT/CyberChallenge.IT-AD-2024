import express from 'express';
import { Sequelize, DataTypes } from 'sequelize';
import { v4 as uuid } from 'uuid';
import jwt from 'jsonwebtoken';

import asyncWrapper from '../express-async-wrapper.mjs';
import HttpError from '../http-error.mjs';

const sequelize = new Sequelize({
  host: 'postgres',
  database: 'auth',
  username: 'authuser',
  password: 'authpass',
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

const User = sequelize.define('User', {
  id: {
    type: DataTypes.UUID,
    defaultValue: Sequelize.UUIDV4,
    primaryKey: true
  },
  username: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true
  },
  password: {
    type: DataTypes.STRING,
    allowNull: false
  }
});

User.beforeCreate((user) => {
  user.id = uuid();
});

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

const router = express.Router();

router.post(
  '/login',
  asyncWrapper(async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
      throw new HttpError(400, 'Invalid credentials');
    }

    const user = await User.findOne({ where: { username, password } });

    if (!user) {
      throw new HttpError(401, 'Invalid credentials');
    }

    const token = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET);

    res.json({ id: user.id, username: user.username, token });
  })
);

router.post(
  '/register',
  asyncWrapper(async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
      throw new HttpError(400, 'Invalid credentials');
    }

    try {
      const user = await User.create({ username, password });
      const token = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET);

      res.json({ id: user.id, username: user.username, token });
    } catch (err) {
      if (err.name === 'SequelizeUniqueConstraintError') {
        throw new HttpError(409, 'Username already exists');
      }

      throw err;
    }
  })
);

const requireLoginMid = (req, res, next) => {
  if (!req.user) {
    res.status(401).json({ err: 'Unauthorized' });
    return;
  }

  next();
};

const setLogingMid = (req, res, next) => {
  if (req.headers.authorization) {
    const token = req.headers.authorization.split(' ')[1];

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      req.user = decoded;
    } catch (err) {
      req.user = null;
    }
  }

  next();
};

export { router as authRouter, requireLoginMid, setLogingMid, dbConnect };
