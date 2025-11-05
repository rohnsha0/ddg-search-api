from openai import OpenAI
import json
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup


class ValidateURLs:
    def __init__(self, access_token: str, insight: str, pp_scope: str, max_results: int):
        print("[INIT] Initializing ValidateURLs class...")
        self.access = access_token
        self.client = OpenAI(api_key=access_token)
        self.insght = insight
        self.ppscope = pp_scope
        self.max_results = max_results
        self.results_per_search = int(max_results/2)
        print("[INIT] ValidateURLs initialized successfully")
        self.SYSTEMPROMPTFORQUERY = """
        You are a specialized AI agent designed to validate project insights and scope information by generating targeted search queries. Your primary objective is to verify the accuracy, completeness, and context of project information found in business intelligence data.

## Core Responsibilities

When provided with project data containing an insights_summary and pp_scope (project scope), you must generate exactly 3 strategic search queries that will help validate:
1. The factual accuracy of key claims
2. The completeness of project details
3. The current status and context of the project

## Query Generation Guidelines

### Query 1: Project Verification
- Focus on verifying the core project announcement
- Include: company name, project type, location, and capacity/scale
- Format: "[Company Name] [Project Type] [Location] [Capacity] [Recent Year]"
- Example: "InSolare Energy BESS project Kolimigundla Andhra Pradesh 600 MW 2025"

### Query 2: Scope and Technical Validation
- Verify technical specifications and scope details
- Include: contracting authority, specific scope elements, technical terms
- Format: "[Contracting Authority] [Technical Scope] [Project Component] tender"
- Example: "SECI balance of system BoS battery storage tender 1200 MWh"

### Query 3: Market Context and Related Developments
- Validate broader market claims and related developments
- Include: market segment, regulatory aspects, or related announcements mentioned
- Format: "[Market Segment] [Country/Region] [Regulatory Body or Context] [Year]"
- Example: "grid scale battery energy storage India SECI 2025"

## Search Query Best Practices

- Keep queries concise: 4-8 words optimal
- Use specific identifiers: company names, project locations, capacities
- Include temporal markers: year or "recent" for current projects
- Avoid special operators: no quotes, no "-" operators, no "site:" operators
- Focus on verifiable facts: numbers, names, locations, dates
- Prioritize official sources: government agencies, industry publications

## Critical Elements to Validate

From insights_summary:
- Company names and their roles
- Project capacity/scale metrics
- Location specificity
- Project stage/status
- Market impact claims
- Service opportunities mentioned

From pp_scope:
- Technical scope accuracy
- Contract duration (e.g., O&M periods)
- Specific deliverables mentioned
- Technical specifications
- Project components

## Error Prevention

- Never include names from ambiguous contexts
- Always use official company names as stated
- Verify location hierarchy (city, state, country)
- Cross-reference numerical values (capacity, duration, cost)
- Confirm regulatory body involvement

## Output Format

Return ONLY the 3 search queries separated by commas, with no additional text, JSON, or formatting.

Example output:
InSolare Energy BESS project Kolimigundla Andhra Pradesh 600 MW 2025, SECI balance of system BoS battery storage tender 1200 MWh, grid scale battery energy storage India SECI 2025

Your goal is to enable efficient validation of project intelligence through strategic, well-crafted search queries that will return authoritative sources confirming or refuting the provided information.
        """
        
        self.SYSTEMPROMPTVALIDATOR= """
You are a precise content verification agent. Your task is to verify whether website HTML content matches the provided article insights and project scope.

## Input Format
You will receive:
1. **HTML Content**: The raw HTML or extracted text from a website
2. **Article Insights**: Expected content, themes, topics, or key information
3. **Project Scope**: Requirements, objectives, or criteria the content should meet

## Verification Process
Analyze the HTML content against the provided criteria:

### Content Matching Criteria
- **Topic Alignment**: Does the HTML content cover the topics mentioned in article insights?
- **Key Information**: Are the essential points, facts, or data from article insights present?
- **Scope Compliance**: Does the content fulfill the project scope requirements?
- **Thematic Consistency**: Does the overall theme and message align?
- **Completeness**: Are all required elements from the scope present?

### Evaluation Rules
- **Exact matching is NOT required** - semantic equivalence is acceptable
- Minor formatting differences should be ignored
- Focus on substantive content, not HTML structure
- Paraphrased content that conveys the same meaning counts as a match
- Missing critical elements reduce the match percentage
- Extra content beyond scope does not cause mismatch (unless it contradicts)

### Match Percentage Calculation
Calculate the percentage based on:
- 100% = All article insights and project scope requirements are fully present
- 75-99% = Most requirements met with minor gaps
- 50-74% = Partial match with significant missing elements
- 25-49% = Minimal overlap with most requirements missing
- 0-24% = Little to no match with the requirements

## Output Format
Return ONLY a valid JSON object with two fields:

```json
{"matches": true, "match_percentage": 95}
```

or

```json
{"matches": false, "match_percentage": 35}
```

### Field Specifications
- **matches**: Boolean value (true if match_percentage >= 70, false otherwise)
- **match_percentage**: Integer from 0 to 100

## Important Rules
- Output ONLY valid JSON with "matches" and "match_percentage" fields
- "matches" must be a boolean (true or false), not a string
- "match_percentage" must be an integer between 0 and 100
- Set "matches" to true if match_percentage >= 70, false otherwise
- Do NOT provide explanations, reasoning, or additional fields
- Do NOT include any text before or after the JSON
- Be strict but fair in your assessment
- Ensure proper JSON formatting with double quotes

## Examples

**Example 1:**
- Article Insights: "Blog post about climate change effects on agriculture"
- Project Scope: "Discuss temperature rise, crop yield impacts, and adaptation strategies"
- HTML: Contains comprehensive sections on global warming, farming challenges, and sustainable practices
- Output: 
```json
{"matches": true, "match_percentage": 95}
```

**Example 2:**
- Article Insights: "Product review of XYZ smartphone with specs and performance"
- Project Scope: "Include camera quality, battery life, and price comparison"
- HTML: Contains camera quality and battery life but missing price comparison
- Output:
```json
{"matches": true, "match_percentage": 75}
```

**Example 3:**
- Article Insights: "Tutorial on Python data structures"
- Project Scope: "Cover lists, dictionaries, sets, and tuples with code examples"
- HTML: Only contains company history and generic marketing text
- Output:
```json
{"matches": false, "match_percentage": 5}
```

**Example 4:**
- Article Insights: "Recipe blog for chocolate chip cookies"
- Project Scope: "Include ingredients, step-by-step instructions, baking time and temperature"
- HTML: Contains ingredients and instructions but missing baking time and temperature
- Output:
```json
{"matches": false, "match_percentage": 65}
```
"""

    def getHTML(self, website: str):
        print(f"[FETCH] Fetching HTML from: {website}")
        try:
            response = requests.get(url=website, timeout=10)
            response.raise_for_status()
            print(f"[FETCH] Successfully fetched HTML (status: {response.status_code})")
            return {"content": response.text, "response_code": response.status_code}
        except requests.RequestException as e:
            print(f"[FETCH] Error fetching HTML: {str(e)}")
            return {"content": str(e), "response_code": 500}
    
    def extract_text_from_html(self, html_content: str, max_chars: int = 50000):
        """
        Extract clean text from HTML and truncate to max_chars.
        This reduces token usage significantly.
        """
        print(f"[EXTRACT] Extracting text from HTML (original size: {len(html_content)} chars)")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            print(f"[EXTRACT] Extracted text size: {len(text)} chars")
            return text
        except Exception as e:
            print(f"[EXTRACT] Error extracting text: {str(e)}")
            # Fallback: simple truncation of HTML
            return html_content[:max_chars] + "... [truncated]"

    def generateSearchQueries(self):
        print("[QUERY-GEN] Generating search queries...")
        response = self.client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": self.SYSTEMPROMPTFORQUERY},
                {
                    "role": "user",
                    "content": f"""
                        Insight Summary: {self.insght}
                        Project Scope: {self.ppscope}
""",
                },
            ],
            response_format={"type": "text"},
        )
        queries = [
            response.strip()
            for response in response.choices[0].message.content.split(",")
            if response
        ]
        print(f"[QUERY-GEN] Generated {len(queries)} search queries: {queries}")
        return queries
    

    def search_links(self, query: str, max_results: int, timelimit: str = 'y'):
        print(f"[SEARCH] Searching for query: '{query}' (max_results={max_results}, timelimit={timelimit})")
        try:
            results = DDGS().text(
                query,
                region='wt-wt',
                safesearch='off',
                timelimit=timelimit,
                max_results=max_results
            )
            
            # Extract only the hrefs
            links = [result['href'] for result in results]
            print(f"[SEARCH] Found {len(links)} links for query: '{query}'")
            print(f"[SEARCH] Links: {links}")
            
            return {
                "success": True,
                "query": query,
                "total_results": len(links),
                "links": links
            }
        except Exception as e:
            print(f"[SEARCH] Error during search: {str(e)}")
            return {
                "errored": str(e)
            }

    def validateHTML(self, content: str):
        # Implement your HTML validation logic here
        print("[VALIDATE] Validating HTML content...")
        print(f"[VALIDATE] HTML content length: {len(content)} characters")
        
        # Extract and truncate text to avoid token limits
        # Rough estimate: 1 token ≈ 4 characters
        # For 200k token limit and system+user prompts, keep content under ~400k chars
        # But we'll be conservative and use 50k chars (~12.5k tokens for content)
        clean_text = self.extract_text_from_html(content, max_chars=50000)
        
        response = self.client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": self.SYSTEMPROMPTVALIDATOR},
                {
                    "role": "user",
                    "content": f"""
                        Insight Summary: {self.insght}
                        Project Scope: {self.ppscope}
                        HTML Content: {clean_text}
""",
                },
            ],
            response_format={"type": "json_object"},
        )

        json_response = json.loads(response.choices[0].message.content)

        print("[VALIDATE] HTML validation response:", json_response)
        return json_response

    def validate(self):
        print("[VALIDATE] Starting validation process'")
        validated_urls= []

        queries = self.generateSearchQueries()
        print(f"[VALIDATE] Processing {len(queries)} generated queries...")
        
        for idx, query in enumerate(queries, 1):
            print(f"\n[VALIDATE] Processing query {idx}/{len(queries)}: '{query}'")
            unvalidated_urls = self.search_links(query=query, max_results=self.results_per_search)

            if unvalidated_urls.get("success"):
                links = unvalidated_urls.get("links", [])
                print(f"[VALIDATE] Validating {len(links)} URLs...")
                
                for url_idx, url in enumerate(links, 1):
                    print(f"[VALIDATE] Processing URL {url_idx}/{len(links)}: {url}")
                    html_content = self.getHTML(website=url)
                    if html_content.get("response_code") == 200:
                        validation_result= self.validateHTML(content=html_content.get("content"))
                        if validation_result.get("matches"):
                            print(f"[VALIDATE] URL validated successfully with match percentage: {validation_result.get('match_percentage')}%")
                            validated_urls.append({
                                "url": url,
                                "match_percentage": validation_result.get("match_percentage")
                            })
                    else:
                        print(f"[VALIDATE] Skipping URL due to non-200 response code: {html_content.get('response_code')}")
            else:
                print(f"[VALIDATE] Search failed with error: {unvalidated_urls.get('errored', 'Unknown error')}")
        
        # Sort by match_percentage (descending) and keep only top self.max_results
        validated_urls.sort(key=lambda x: x['match_percentage'], reverse=True)
        top_validated_urls = validated_urls[:self.max_results]
        
        print("\n[VALIDATE] Validation process completed")
        print(f"[VALIDATE] Total validated URLs before filtering: {len(validated_urls)}")
        print(f"[VALIDATE] Top {len(top_validated_urls)} URLs with highest match percentages retained")
        print(f"[VALIDATE] Insights: {self.insght} and Scope: {self.ppscope}")
        
        return top_validated_urls
