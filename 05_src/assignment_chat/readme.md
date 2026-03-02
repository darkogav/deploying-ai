# A AI chat client that helps students search for faculty in Economics

This chat uses chromadb to create a searchable database from the included data file data.csv. 

The db is stored locally on the file system and is preserved upon agent shutdown.

The agent app is makes of three files
- econapp.py
- prompts.py
- main.py 

The econapp.py file does all the work. It creates a chroma_db from the csv file. It establishes a connection to OpenAI using a .secrets file.  It cals OpenALex to get citations for faculty and returns formatted results. 

The prompts.py file contains guardrails tested and optimize to return results ONLY from the local dataset and OpenAlex API for found citations. 

The main.py file is the main execution file that builds the guardrails app server. To run this applicaiton, you need to run the main.py file and launch a web browser and go to: 

http://127.0.0.1/econapp

