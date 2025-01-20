import multer from 'multer';
import path from 'path';
import fs from 'fs';
import pdfParse from 'pdf-parse/lib/pdf-parse.js';
import { CharacterTextSplitter } from '../helpers/TextSplitter.js';
import { HfInference } from "@huggingface/inference";
import { ChromaClient } from "chromadb";

// Setup multer for file uploads
const uploadDir = 'tmp/';
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`),
});
const upload = multer({ storage }).array('files');

// Initialize Hugging Face Inference API
const hf = new HfInference(process.env.HUGGINGFACE_TOKEN);

// Initialize ChromaDB Client
let collection;
(async () => {
  const client = new ChromaClient({
    path: "http://127.0.0.1:5050",  // Custom URL and port
  });
  
  // Try to get the collection by name
  const collections = await client.listCollections();
  collection = collections.find(col => col === "my_collection");

  // If the collection doesn't exist, create it
  if (!collection) {
    collection = await client.createCollection({
      name: "my_collection",
    });
  }
})();

// Upload and process PDFs
export const uploadPDF = (req, res) => {
  upload(req, res, async (err) => {
    if (err) {
      return res.status(500).json({ message: 'File upload failed', error: err.message });
    }
    if (!req.files) {
      return res.status(400).json({ message: 'No files uploaded' });
    }

    let fileContents = [];

    // Read and parse PDF files
    for (const file of req.files) {
      const filePath = path.join(uploadDir, file.filename);
      try {
        const dataBuffer = fs.readFileSync(filePath);
        const pdfData = await pdfParse(dataBuffer);
        fileContents.push({ filename: file.originalname, content: pdfData.text });
        fs.unlinkSync(filePath);  // Delete the file after processing
      } catch (readErr) {
        console.error(`Error processing file ${file.originalname}:`, readErr);
      }
    }

    const rawText = fileContents.map(file => file.content).join("\n");

    // Use CharacterTextSplitter to split the text
    const splitter = new CharacterTextSplitter("\n", { chunkSize: 1000, chunkOverlap: 200 });
    const textChunks = splitter.splitText(rawText);

    // Generate embeddings using Hugging Face Inference API and store in ChromaDB
    await Promise.all(
      textChunks.map(async (chunk, index) => {
        const response = await hf.featureExtraction({
          model: "sentence-transformers/all-MiniLM-L6-v2",
          inputs: chunk,
        });

        const embedding = Array.isArray(response) ? response[0] : response;

        await collection.upsert({
          ids: [`chunk_${index}`],
          embeddings: [embedding],
          documents: [chunk],
          metadatas: [{ chunk_index: index }],
        });
      })
    );

    res.status(200).json({ message: 'Files processed and embeddings stored in ChromaDB successfully!' });
  });
};

// Query function with Gemini model
export const askQuery = async (req, res) => {
  const { query } = req.body;

  try {
    // Generate embedding for the query
    const response = await hf.featureExtraction({
      model: "sentence-transformers/all-MiniLM-L6-v2",
      inputs: query,
    });

    const queryEmbedding = Array.isArray(response) ? response[0] : response;

    // Search for similar embeddings in ChromaDB
    const results = await collection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: 5,
    });

    // Retrieve the relevant documents
    const retrievedText = results.documents.flat().join("\n");

    // Generate a response using Gemini model
    const prompt = `Based on the following information, answer the user's question:\n\n${retrievedText}\n\nIf the question isn't present in the text, you can answer based on your knowledge.\n\nUser's question: ${query}`;

    const model = genAI.getGenerativeModel({ model: "gemini-pro" });
    const aiResponse = await model.generateContent(prompt);

    const generatedText = aiResponse.response.text();

    res.status(200).json({ response: generatedText });
  } catch (error) {
    console.error('Error during query:', error);
    res.status(500).json({ message: 'Error processing query', error: error.message });
  }
};

