// handlers/mongodb.js
const { MongoClient, ServerApiVersion } = require('mongodb');
const { MONGODB } = require('../config');

const uri = MONGODB;

const client = new MongoClient(uri, {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: true,
      deprecationErrors: true,
    }
  });

let db;

async function connectMongo() {
    try {
        await client.connect();
        db = client.db('DivAPI');
        console.log('Connected to MongoDB');
    } catch (error) {
        console.error('Error connecting to MongoDB:', error);
    }
}

function getDb() {
    if (!db) {
    }
    return db;
}

module.exports = { connectMongo, getDb };
