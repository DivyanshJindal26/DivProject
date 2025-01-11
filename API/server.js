import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

import logger from './middleware/logger.js';
import auth from './middleware/auth.js';
import notFound from './middleware/notFound.js';
import errorHandler from './middleware/error.js'
import userRoutes from './routes/user.js';
// import ragRoutes from './routes/rag.js';
// import todoRoutes from './routes/todo.js';
// import translateRoutes from './routes/translate.js';
import { connectMongo } from './helpers/mongodb.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const port = process.env.PORT || 5000;

const app = express();

// Connect to MongoDB
connectMongo();

// Body parser middleware
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// Logging middleware
app.use(logger);
app.use(auth);

// setting up routes
app.use('/api/user', userRoutes);
// app.use('/api/todo', todoRoutes);
// app.use('/api/rag', ragRoutes);
// app.use('/api/translate', translateRoutes);

// Error handler
app.use(notFound);
app.use(errorHandler);

app.listen(port, () => console.log(`Server is running on port ${port}`));