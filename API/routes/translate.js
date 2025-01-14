import express from 'express';
import { sendPhrases, checkAns } from '../controllers/translate.js';

const router = express.Router();

router.post('/send_phrases', sendPhrases);
router.post('/check_answer', checkAns);
export default router;