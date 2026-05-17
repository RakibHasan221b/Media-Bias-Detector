import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file!")

if not api_key.startswith("sk-proj-"):
    raise ValueError("❌ Invalid API key format!")

client = OpenAI(api_key=api_key)
print("✅ OpenAI client initialized successfully\n")


class BiasEngine:
    """Main class - Generates bias analysis using gpt-4o-mini"""
    
    def analyze(self, bd_texts, intl_texts, topic, start_date, end_date):
        # Same slicing as evaluator to avoid mismatch
        bd_block = "\n\n---\n\n".join([text[:2500] for text in bd_texts[:6]])
        intl_block = "\n\n---\n\n".join([text[:2500] for text in intl_texts[:6]])

        prompt = f"""You are an expert media bias analyst with knowledge of communication research. Analyze BOTH sides fairly and objectively using the provided texts only.

**TOPIC:** {topic}
**TIME PERIOD:** {start_date} to {end_date}

**BANGLADESHI MEDIA COVERAGE:**
{bd_block}

**INTERNATIONAL MEDIA COVERAGE:**
{intl_block}

**Strict Rules:**
- Base EVERY claim strictly on the provided texts ONLY. Do NOT hallucinate or invent any information.
- If something is not explicitly mentioned in the texts, state "Not mentioned in the provided articles."
- Always support points with direct quotes and clearly mention which side (Bangladeshi or International).
- Never add context, events, quotes, names, or implications that are not directly present in the given texts.
- Analyze both sides equally. Do not favor one side.
- Clearly state if one side has limited or no relevant coverage.

Perform the analysis in exactly these 5 steps:

1. **BD Narrative Summary**  
   Summarize the main narrative, key arguments, tone, framing, and emphasis in Bangladeshi media. Support with direct quotes.

2. **International Narrative Summary**  
   Summarize the main narrative, key arguments, tone, framing, and emphasis in International media. Support with direct quotes.

3. **Framing Comparison**  
   Compare how the same issue is framed differently between Bangladeshi and International media. Analyze differences in problem definition, causal interpretation, moral evaluation, emphasis vs omission, and language choices.

4. **Bias Detection**  
   Identify specific biases in **both** Bangladeshi and International media with clear evidence:
   - Selection/Omission Bias (what was included or left out)
   - Framing Bias (how the story is packaged)
   - Linguistic Bias (emotional language, loaded terms, labeling)
   - Sourcing Bias (whose voices are prioritized or ignored)
   - Nationalistic, Ideological, or Political Bias (if present)

5. **Overall Conclusion**  
   Provide a balanced academic assessment:
   - Which side (if any) shows stronger or more frequent bias and in what forms?
   - Most significant framing and tonal differences between the two.
   - Notable patterns observed on either side.
   - Implications for information quality and audience perception.

Maintain a strictly neutral, objective, and academic tone throughout. Be evidence-based and fair to both sides."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a precise, evidence-based media bias analyst. Always remain neutral and analyze both sides fairly. Never hallucinate."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.25
        )

        return response.choices[0].message.content


class BiasEvaluator:
    """Evaluator class - Uses gpt-4o"""
    
    def evaluate(self, analysis_text: str, bd_texts, intl_texts, topic, start_date, end_date):
        
        # Same slicing as analyzer
        bd_block = "\n\n---\n\n".join([text[:2500] for text in bd_texts[:6]])
        intl_block = "\n\n---\n\n".join([text[:2500] for text in intl_texts[:6]])

        eval_prompt = f"""You are a strict academic evaluator.

**Topic:** {topic}
**Time Period:** {start_date} to {end_date}

**Original Selected Bangladeshi Articles:**
{bd_block}

**Original Selected International Articles:**
{intl_block}

**Generated Analysis to Evaluate:**
{analysis_text}

Evaluate this analysis based on the original articles provided above.

Rate each criterion from 1 to 10 with short justification:

1. **Fidelity to Texts** (Accuracy and no hallucination)
2. **Balance & Fairness** (Treats both sides fairly)
3. **Evidence Quality** (Use of direct quotes and examples)
4. **Framing Analysis Depth**
5. **Bias Detection Accuracy** (on both sides)
6. **Structure & Clarity**
7. **Overall Objectivity**

Finally, give an **Overall Score** (out of 10) and a short final comment."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a highly critical, fair, and detailed academic evaluator."},
                {"role": "user", "content": eval_prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )

        return response.choices[0].message.content