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
 



---

### 🧾 How it looks (rendered on GitHub)

> (GitHub renders Mermaid directly — when you push this to your README, it will display as an interactive flowchart)

🔹 **Inputs**  
→ FPL API for your team & fixtures  
→ Serper/Scrape tools for news and expert opinions  

⬇️  
🧩 **CrewAI Agents** (News, Experts, Team, Opponents, Strategist) work sequentially  
⬇️  
🏁 **Output:** a clear, human-readable weekly strategy (Transfers, Captain, XI, Chip).

---

### Optional — a variant for more “technical” viewers
If you want to show components + data exchange:

```markdown
```mermaid
graph LR
    subgraph User["👤 User"]
        U1["Run.py\n(--gw, --entry, --h2h)"]
    end

    subgraph Context["🗂️ Context Builder"]
        C1["fpl_api.py\n→ fetch JSON data"]
        C2["news_tools.py\n→ Serper + ScrapeWebsiteTool"]
    end

    subgraph Crew["🤖 CrewAI Agents"]
        N["NewsAgent"]
        E["ExpertsAgent"]
        T["TeamAgent"]
        O["OpponentsAgent"]
        S["StrategistAgent"]
    end

    subgraph Output["📊 Recommendation"]
        R["Final plan: transfers, captain, chip, XI"]
    end

    U1 --> C1
    U1 --> C2
    C1 --> T
    C1 --> O
    C2 --> N
    C2 --> E
    N --> S
    E --> S
    T --> S
    O --> S
    S --> R
