import { getDb } from '../helpers/mongodb.js';
import { encrypt, decrypt } from '../helpers/crypto.js';
import { sendEmail } from '../helpers/otpsender.js';

import jwt from 'jsonwebtoken';

// @desc creating a new user
// @route POST /api/user/create
export const userCreate = async (req, res, next) => {
  try {
    const db = getDb();
    const { username, password, email } = req.body;
    if (!username || !password || !email) {
      return res.status(400).json({ message: 'Missing username, password, or email' });
    }

    const existingUser = await db.collection('users').findOne({ email });
    if (existingUser) {
      return res.status(409).json({ message: 'User already exists' });
    }

    const hashedPassword = encrypt(password);

    await db.collection('users').insertOne({
      username,
      password: hashedPassword,
      email,
      createdAt: new Date(),
    });

    res.status(201).json({ message: 'User successfully created' });
  } catch (error) {
    console.error('Error creating user:', error);
    res.status(500).json({ message: 'Server error. Please try again later.' });
  }
};

// @desc logging in a user
// @route POST /api/user/login
export const userLogin = async (req, res, next) => {
  const { email, password } = req.body;
  const db = getDb();
  if (!email || !password) {
    return res.status(400).json({ message: 'Missing email or password' });
  }
  const user = await db.collection('users').findOne({ email });
  if (!user) {
    return res.status(404).json({ message: 'User not found' });
  }
  if (decrypt(user.password) !== password) {
    return res.status(401).json({ message: 'Invalid password' });
  }
  const token = jwt.sign({ username: user.username }, process.env.JWT_SECRET, { algorithm: 'HS256', expiresIn: '1h' });
  await db.collection('users').updateOne({ password: user.password }, { $set: { token } });
  return res.status(200).json({ message: 'Successfully logged in', token });
};

// @desc forgot password and request for OTP
// @route POST /api/user/forgot-password
export const userForget = async (req, res, next) => {
  const { email } = req.body;
  const db = await getDb();
  if (!email) {
    return res.status(400).json({ message: 'Missing email' });
  }
  const user = await db.collection('users').findOne({ email });
  if (!user) {
    return res.status(404).json({ message: 'User not found' });
  }

  const otp = Math.floor(100000 + Math.random() * 900000);
  const hashedOtp = encrypt(otp);
  await sendEmail(email, otp)
  await db.collection('users').updateOne({ email }, { $set: { reset_otp: hashedOtp } });
  res.status(200).json({ message: 'OTP sent to your email' });
};

// @desc verify OTP and reset password
// @route POST /api/user/verify-otp
export const userVerifyOTP = async (req, res, next) => {
  const db = await getDb();
  const { email, otp, newpwd } = req.body;
  const user = await db.collection('users').findOne({ email });
  const storedOtp = user.reset_otp;
  if (!storedOtp) {
    return res.status(400).json({ message: 'No OTP found. Please request a new OTP.' });
  }
  if (decrypt(storedOtp) !== otp) {
    return res.status(400).json({ message: 'Invalid OTP' });
  }
  await db.collection('users').updateOne(
    { email },
    {
      $unset: { reset_otp: '' },
      $set: { password: encrypt(newpwd) }
    }
  );  
  res.status(200).json({ message: 'Password successfully changed' });
};


// @desc logout a user
// @route POST /api/user/logout
export const userLogout = async (req, res, next) => {
  const db = await getDb();
  const user = db.collection('users').findOne({ token: req.body.token });
  if (!user) {
    return res.status(404).json({ message: 'User not found. Login again' });
  }
  await db.collection('users').updateOne({ token: user.token }, { $unset: { token: '' } });
  await db.collection('discord').updateOne({ tokens: user.token }, { $unset: { tokens: '' } });
  res.status(200).json({ message: 'Successfully logged out' });
};

// @desc get all users
// @route GET /api/user
export const userGetAll = async (req, res, next) => {
  const db = await getDb();
  const userList = [];
  const users = db.collection('users').find();
  users.forEach(user => {
    userList.push({ username: user.username, email: user.email });
  });
  return res.status(200).json({ users: userList });
};