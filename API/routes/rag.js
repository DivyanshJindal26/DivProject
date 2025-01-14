import express from 'express';

import { uploadPDF, askQuery, uploadPDFMiddleware  } from '../controllers/rag.js';

const router = express.Router();
router.post('/uploadpdf', uploadPDFMiddleware, uploadPDF);
router.post('/query', askQuery);

export default router;