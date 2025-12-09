# services/LLM_formatter.py
import json
import openai
import os

# Set your API key (optional if testing with mock)
openai.api_key = os.getenv("OPENAI_API_KEY")

def format_as_bibtex(metadata: dict, style: str = "bibtex", model: str = "gpt-3.5-turbo", use_mock: bool = True) -> str:
    """
    Format metadata dict as a BibTeX entry using OpenAI LLM.
    If use_mock=True, returns a simple mock entry for testing.
    """
    if use_mock:
        # Mock for testing
        return f"""@article{{auto2025,
  title={{ {metadata.get('title','UNKNOWN')} }},
  author={{ {' & '.join(metadata.get('author',[]))} }},
  year={{ {metadata.get('year','')} }}
}}"""

    # Real LLM call
    prompt = f"""You are a citation formatter.
Given the following metadata, output a single BibTeX entry of type @{metadata.get('type','article')}.
Include all non-empty fields and use the key 'auto2025'.

Metadata:
```json
{json.dumps(metadata, indent=2)}
```"""

    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=150,
    )

    return response.choices[0].message.content.strip()
