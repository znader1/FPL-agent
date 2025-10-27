# FPL-Agent
Personal multi-agent assistant built with CrewAI to plan Fantasy Premier League transfers.

## Features
- Reads live data from the official FPL API  
- Analyzes player form, injury news, and expected points  
- Suggests transfers, captain/vice, and bench plan  
- Built with CrewAI + LangChain + OpenAI GPT-4o-mini  

## Run
```bash
pip install -r requirements.txt
cp .env.example .env # set your open AI key
python crew.py
 