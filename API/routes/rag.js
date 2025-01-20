import express from 'express';

import { uploadPDF, askQuery  } from '../controllers/rag.js';

const router = express.Router();
router.post('/uploadpdf', uploadPDF);
router.post('/query', askQuery);

export default router;