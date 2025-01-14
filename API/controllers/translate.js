import { GoogleGenerativeAI } from "@google/generative-ai";

// @desc Send phrases for translation to Gemini
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
        You will receive a list of English phrases and a target language. 
        Translate each phrase into the target language. 
        Remove any special characters in English-written languages. 
        For example, convert ú to u, Ñ to N, etc. 
        Respond ONLY with a JSON object like:
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
      Phrases: ${JSON.stringify(phrases.split(', '))}
    `;

    const result = await model.generateContent(prompt, generationConfig);
    console.log();
    const responseText = result?.response?.candidates?.[0]?.content;

    if (!responseText) {
      throw new Error("No response from the AI model.");
    }

    let translation;
    try {
      translation = JSON.parse(result.response?.candidates?.[0]?.content?.parts?.[0]?.text?.replace(/```json\n?|```/g, '')?.trim());
    } catch (parseError) {
      console.error('Error parsing AI response:', parseError);
      return res.status(500).json({ message: 'Invalid response format from AI.' });
    }

    res.status(200).json({ translation });

  } catch (error) {
    console.error('Error translating phrases:', error);
    res.status(500).json({ message: 'Error translating phrases', error: error.message });
  }
};

export const checkAns = async (req, res, next) => {
  const { correct_answer, user_answer } = req.body;
  if(!correct_answer || !user_answer) {
    return res.status(400).json({ message: 'Correct answer and user answer are required.' });
  }
  const is_correct = user_answer.trim().toLowerCase() === correct_answer.trim().toLowerCase();
  res.status(200).json({ is_correct });
}