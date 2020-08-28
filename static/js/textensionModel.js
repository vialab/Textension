// ES5 class for abstracting the data behind textensions OCR interactions 

// class OCRModel

class TextensionModel {
    constructor( ocr, translation, word_blocks ) {
        this.setOCR(ocr)

        this.setTranslation(translation)

        this.setWordBlocks(word_blocks)
    }

    setOCR( ocr ) {
        this.ocr = ocr
    }


    setTranslation( translation ) {
        this.translation = translation
    }

    setWordBlocks( wordBlocks ) {
        this.wordBlocks = wordBlocks

        for (const key in this.wordBlocks) {
            if (this.wordBlocks.hasOwnProperty(key)) {
                const block = this.wordBlocks[key];
                
                for (const lkey in block) {
                    if (block.hasOwnProperty(lkey)) {
                        const line = block[lkey]

                        const ocrLine = this.ocr[key][lkey]//[lkey]
                        
                        for (const wkey in line) {
                            if (line.hasOwnProperty(wkey)) {
                                const word = line[wkey];

                                if (word.confidence < ocrLine[1]) {
                                    // single word confidence is lower than whole line confidence, lets take that word from that line
                                    
                                    let ocrWords = ocrLine[0].split(" ")

                                    if (ocrWords.length == line.lenth) {
                                        // console.log("replacing: ", word.text, "  with ", ocrWords[word.word_pos],ocrWords)
    
                                        word.text = ocrWords[word.word_pos]
                                    }
                                }
                            }
                        }
                    }
                }

            }
        }

        word_blocks = this.wordBlocks
    }
}