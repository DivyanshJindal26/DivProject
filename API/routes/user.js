import express from 'express';
import { userCreate, userLogin, userForget, userVerifyOTP, userLogout, userGetAll } from '../controllers/user.js';

const router = express.Router();

router.post('/create', userCreate);
router.post('/login', userLogin);
router.post('/forgot-password', userForget);
router.post('/verify-otp', userVerifyOTP);
router.post('/logout', userLogout);
router.get('/', userGetAll)

export default router;