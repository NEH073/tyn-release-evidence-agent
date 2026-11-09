\# TYN Release Evidence Agent



An AI-powered Jira Release Evidence Agent built for The Yellow Network AI Engineer Assessment.



The agent investigates software release requirements using Jira tools, evaluates linked evidence and comments, and produces an evidence-based release-readiness report.



\## 1. Technology Stack



\- Python 3.12

\- LangChain and LangGraph

\- Google Gemini (`gemini-3.5-flash-lite`)

\- Jira Cloud REST API

\- Pydantic

\- Requests

\- python-dotenv



\## 2. Architecture



The application has two main stages.



\### Jira Dataset Import



`src/import\_jira.py` imports the supplied assessment dataset into a dedicated Jira project.



It:

\- Creates Jira issues from source records.

\- Preserves source IDs and record details in Jira descriptions.

\- Imports comments with original fictional event text.

\- Preserves scenario actor, role and event timestamp in comment bodies.

\- Creates Jira relationships.

\- Saves source-ID-to-Jira-key mappings in `reports/issue\_mapping.json`.



The assessment agent retrieves evidence from Jira rather than reading the dataset JSON directly.



\### AI Evidence Investigation



`src/src/agent.py` runs a LangGraph ReAct agent.



The agent:

1\. Retrieves the release manifest from Jira.

2\. Identifies mandatory linked requirements.

3\. Investigates requirements using Jira tools.

4\. Retrieves relevant issue descriptions, comments and linked issues.

5\. Evaluates evidence against the target release configuration.

6\. Produces a decision, explanation and outstanding verification.

7\. Calculates the overall release decision.

8\. Saves the assessment report and investigation trace.



\### Jira Tools



Implemented in `src/src/jira\_tools.py`:



\- `get\_jira\_issue`: retrieves an issue, comments and linked issues.

\- `search\_jira\_issues`: searches issues within the assessment dataset scope.



\## 3. Project Structure



```text

tyn-release-agent/

├── inputs/

│   └── dataset.json

├── reports/

│   ├── issue\_mapping.json

│   └── assessment\_R2.4\_recheck.md

├── src/

│   ├── import\_jira.py

│   ├── test\_gemini\_tools.py

│   └── src/

│       ├── agent.py

│       ├── jira\_tools.py

│       └── test\_jira\_tool.py

├── traces/

│   └── assessment\_R2.4\_recheck.json

├── .env.example

├── .gitignore

├── requirements.txt

└── README.md

```



\## 4. Configuration



Python 3.12 is recommended.



Create and activate a virtual environment:



```powershell

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



Install dependencies:



```powershell

python -m pip install -r requirements.txt

```



Create a `.env` file using `.env.example` as a template.



Configure these variables:



```env

JIRA\_BASE\_URL=https://your-domain.atlassian.net

JIRA\_EMAIL=your-email@example.com

JIRA\_API\_TOKEN=your-jira-api-token

JIRA\_PROJECT\_KEY=TYN

GOOGLE\_API\_KEY=your-google-api-key

```



Do not commit `.env` or expose API tokens.



\## 5. Jira Dataset Import



The dataset is expected at `inputs/dataset.json`.



For a fresh Jira project, import issues and comments:



```powershell

python .\\src\\import\_jira.py --limit 400

```



After all source records have been mapped, create relationships:



```powershell

python .\\src\\import\_jira.py --limit 400 --links

```



The completed assessment import contains:



\- 400 Jira issues

\- 2,059 comments

\- 76 unique Jira relationships



The importer writes its mapping to `reports/issue\_mapping.json`.



Do not rerun link import against an already populated project without first verifying existing relationships.



\## 6. Run the Agent



From the project root, with the virtual environment activated:



```powershell

python .\\src\\src\\agent.py

```



Current assessment configuration:



\- Jira project: `TYN`

\- Dataset label: `tyn-release-assessment-v2`

\- Target release: `R2.4`

\- Commit: `b7a91f2`

\- Prompt version: `p7`

\- Environment: `production`

\- Service: `atlas-assistant`

\- Release manifest: `TYN-360`



\## 7. Output Artifacts



\### Assessment report



`reports/assessment\_R2.4\_recheck.md`



Contains requirement IDs, Jira references, decisions, explanations, evidence and outstanding verification.



\### Investigation trace



`traces/assessment\_R2.4\_recheck.json`



Contains release configuration, requirement investigation


## 13. Model Usage Metrics

Model: `gemini-3.5-flash-lite`

Aggregated across the 12 requirement investigations:

| Metric | Value |
|---|---:|
| Input tokens | 143,618 |
| Output tokens | 6,021 |
| Total tokens | 149,639 |
| End-to-end runtime | 156.90 seconds |

Token counts are aggregated from the usage metadata returned by the model across individual invocations. Repeated context sent in separate requests is counted again.
