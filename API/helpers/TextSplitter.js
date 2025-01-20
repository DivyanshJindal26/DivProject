class TextSplitter {
    constructor(opts = {}) {
      this.chunkSize = opts.chunkSize || 1000;
      this.chunkOverlap = opts.chunkOverlap || 200;
      this.chunk = opts.chunk || false;
    }
  
    createChunks(texts, separator) {
      const chunks = [];
      let currentChunk = [];
  
      for (const text of texts) {
        if (currentChunk.join(separator).length + text.length + separator.length <= this.chunkSize) {
          currentChunk.push(text);
        } else {
          if (currentChunk.length) {
            chunks.push(currentChunk.join(separator));
          }
          currentChunk = [text];
        }
      }
  
      if (currentChunk.length) {
        chunks.push(currentChunk.join(separator));
      }
  
      return chunks;
    }
  }
  
export class CharacterTextSplitter extends TextSplitter {
  constructor(character = "\n\n", opts) {
    super(opts);
    this.character = character;
  }

  splitText(text, opts) {
    const texts = text.split(this.character).map((t) => t.trim());
    return (opts && opts.chunk) || this.chunk
      ? this.createChunks(texts, this.character)
      : texts.filter((t) => t.length);
  }
}
