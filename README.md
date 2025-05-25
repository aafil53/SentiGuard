A Chrome Extension + FastAPI ML Backend that detects and blocks toxic or hateful comments in YouTube livestreams and comment sections — in real time.

//How It Works

1.content.js monitors new comments on YouTube via DOM mutations.

2.Comments are batched and sent to the FastAPI /check endpoint.

3.The ML backend classifies the text using unitary/toxic-bert.

4.If the toxicity score exceeds the threshold (default: 0.7), the comment is hidden.

5.User can toggle filtering and adjust threshold via popup interface.



//How to run:
python app.py
