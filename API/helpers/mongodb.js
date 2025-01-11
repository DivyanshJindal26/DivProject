import { MongoClient, ServerApiVersion } from 'mongodb';

const uri = process.env.MONGODB;

if (!uri) {
  throw new Error('MONGODB URI is not defined in environment variables');
}

const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
});

let db;

export async function connectMongo() {
  try {
    await client.connect();
    db = client.db('DivAPI');
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    process.exit(1);
  }
}

export function getDb() {
  if (!db) {
    throw new Error('Database not connected. Call connectMongo() first.');
  }
  return db;
}
