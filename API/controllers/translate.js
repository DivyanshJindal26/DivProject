import { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } from "@google/generative-ai";

// @desc send phrases for translation to gemini
// @route POST /api/translate/send_phrases
export const sendPhrases = async (req, res, next) => {
  const { phrases, language } = req.body;

  if (!phrases || !language) {
    return res.status(400).json({ message: 'Phrases and language are required.' });
  }

  const apiKey = process.env.GEMINI_API_KEY;

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({
      model: "gemini-2.0-flash-exp",
      systemInstruction: `
        Take the list of phrases given in English and convert them to the given language. 
        Remove any special characters in English-written languages. 
        Like convert ú to u, Ñ into N, and so on. 
        Respond ONLY with a JSON object. Example: 
        {"hello":"hola","me":"yo"}
      `,
    });

    const generationConfig = {
      temperature: 1,
      topP: 0.95,
      topK: 40,
      responseMimeType: "application/json",
    };

    const prompt = `
      Language: ${language}
      Phrases: ${JSON.stringify(phrases)}
    `;

    const result = await model.generateContent(prompt, generationConfig);
    const responseText = result?.response?.text || result?.text;

    console.log('Translation Response:', responseText);
    res.status(200).json({ translation: JSON.parse(responseText) });

  } catch (error) {
    console.error('Error translating phrases:', error);
    res.status(500).json({ message: 'Error translating phrases', error: error.message });
  }
};
