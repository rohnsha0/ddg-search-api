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
        print("[INIT] ValidateURLs initialized successfully")
        self.SYSTEMPROMPTFORQUERY = """
You are an intelligent assistant that generates precise web search queries to verify the authenticity of new project or investment announcements.

Inputs Provided:

* Insights Summary → a short paragraph summarizing the article or announcement.
* Project Scope → a description of what the project involves or covers.

Your Task:

1. Identify the core entities from the inputs — including companies, investment amounts, locations, industries, project types, and key years.
2. Generate a concise, keyword-rich search query to help verify the authenticity of the news on reliable business or financial sites.
3. Prioritize credible domains such as:
   reuters.com, bloomberg.com, bbc.com, economictimes.indiatimes.com, business-standard.com, livemint.com, thehindu.com
4. The query should be formatted for direct use on Google or Bing.
5. The final output must be plain text in the following structure:

Example Input:
Insights Summary: DP World has pledged an additional $5 billion investment in India to bolster its supply chain network, following MoUs with Gujarat state for new ports and terminals.
Project Scope: Development of new ports, terminals, and logistics zones across India, especially Gujarat.

Example Output:
DP World $5 billion investment India Gujarat ports terminals 2025"}
"""


        self.SYSTEMPROMPTVALIDATOR= """
You are a flexible content verification agent. Your task is to verify whether website HTML content aligns with the provided article insights and project scope based on overall meaning and intent.

## Input Format
You will receive:
1. **HTML Content**: The raw HTML or extracted text from a website
2. **Article Insights**: Expected content, themes, topics, or key information
3. **Project Scope**: Requirements, objectives, or criteria the content should meet

## Verification Process
Analyze the HTML content against the provided criteria with flexibility:

### Content Matching Criteria
- **Overall Meaning**: Does the HTML content convey the same general meaning and intent as the article insights?
- **Topic Alignment**: Does the content cover the main topics or themes mentioned?
- **Key Information**: Are the essential points or facts present, even if worded differently?
- **Thematic Consistency**: Does the overall theme and message align with the expectations?

### Evaluation Philosophy
- **Flexibility is key**: Even if the article has limited data, it should match if the overall meaning aligns
- **Focus on substance over quantity**: A concise article that captures the essence is a match
- **Semantic equivalence**: Different words expressing the same idea count as a match
- **Context matters**: Consider the broader context and intent, not just keyword matching
- **Partial information is acceptable**: If the available information aligns with the scope, it's a match
- **Ignore formatting and structure**: Focus only on the content's meaning
- **Don't penalize brevity**: Short content that accurately reflects the insights is still a match

### When to Mark as TRUE (matches)
- The HTML content addresses the main topic/theme from the insights
- Key facts or information from insights are present (even if briefly mentioned)
- The overall narrative or message aligns with the project scope
- The content provides relevant information about the subject matter
- Even if details are sparse, the core meaning is captured

### When to Mark as FALSE (matches)
- The HTML content is about a completely different topic
- None of the key information from insights is present
- The content contradicts the expected information
- The website is clearly unrelated to the project scope

## Output Format
Return ONLY a valid JSON object with one field:

```json
{"matches": true}
```

or

```json
{"matches": false}
```

### Field Specifications
- **matches**: Boolean value (true or false) based on whether the content aligns with the overall meaning
- Do NOT include any other fields like "match_percentage" or "explanation"

## Important Rules
- Output ONLY valid JSON with the "matches" field
- "matches" must be a boolean (true or false), not a string
- Be generous in your assessment - focus on overall alignment, not strict compliance
- Do NOT provide explanations, reasoning, or additional fields
- Do NOT include any text before or after the JSON
- Err on the side of matching if the core meaning aligns, even with limited data

## Examples

**Example 1:**
- Article Insights: "InSolare Energy announces 600 MW BESS project in Kolimigundla, Andhra Pradesh"
- Project Scope: "Verify project announcement, company name, location, and capacity"
- HTML: Contains a brief news article mentioning InSolare's battery storage project in Andhra Pradesh with 600 MW capacity
- Output: 
```json
{"matches": true}
```

**Example 2:**
- Article Insights: "SECI issues tender for balance of system for 1200 MWh battery storage"
- Project Scope: "Verify tender announcement and technical scope"
- HTML: Contains tender notice from SECI about battery storage BoS work, mentions scope details
- Output:
```json
{"matches": true}
```

**Example 3:**
- Article Insights: "Grid-scale battery energy storage projects in India"
- Project Scope: "Market overview of BESS sector in India"
- HTML: Article about solar panel manufacturing in Europe
- Output:
```json
{"matches": false}
```

**Example 4:**
- Article Insights: "Recipe blog for chocolate chip cookies"
- Project Scope: "Include ingredients and instructions"
- HTML: Contains company financial reports and stock market data
- Output:
```json
{"matches": false}
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

    def generateSearchQueries(self):
        print("[QUERY-GEN] Generating search queries...")
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
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
        print("[VALIDATE] Validating HTML content...")
        print(f"[VALIDATE] HTML content length: {len(content)} characters")
        
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": self.SYSTEMPROMPTVALIDATOR},
                {
                    "role": "user",
                    "content": f"""
                        Insight Summary: {self.insght}
                        Project Scope: {self.ppscope}
                        HTML Content: {content}
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
        unvalidated_links= []

        queries = self.generateSearchQueries()
        print(f"[VALIDATE] Processing {len(queries)} generated queries...")
        
        for idx, query in enumerate(queries, 1):
            print(f"\n[VALIDATE] Processing query {idx}/{len(queries)}: '{query}'")
            unvalidated_urls = self.search_links(query=query, max_results=self.max_results)
            unvalidated_links.extend(unvalidated_urls)
            print(f"[VALIDATE] Search results: {unvalidated_urls}")

            if unvalidated_urls.get("success"):
                links = unvalidated_urls.get("links", [])
                print(f"[VALIDATE] Validating {len(links)} URLs...")
                
                for url_idx, url in enumerate(links, 1):
                    print(f"[VALIDATE] Processing URL {url_idx}/{len(links)}: {url}")
                    html_content = self.getHTML(website=url)
                    if html_content.get("response_code") == 200:
                        try:
                            validation_result = self.validateHTML(content=html_content.get("content"))
                            matches = validation_result.get("matches", False)
                            
                            # Collect all URLs that match
                            if matches:
                                print("[VALIDATE] URL validated successfully - content matches")
                                validated_urls.append({"url": url})
                            else:
                                print("[VALIDATE] URL does not match - content does not align")
                        except Exception as e:
                            print(f"[VALIDATE] Error during validation of URL: {str(e)}")
                            continue
                    else:
                        print(f"[VALIDATE] Skipping URL due to non-200 response code: {html_content.get('response_code')}")
            else:
                print(f"[VALIDATE] Search failed with error: {unvalidated_urls.get('errored', 'Unknown error')}")

        # Keep only the first self.max_results validated URLs
        if len(validated_urls) > self.max_results:
            top_validated_urls = validated_urls[:self.max_results]
        else:
            top_validated_urls = validated_urls

        print("\n[VALIDATE] Validation process completed")
        print(f"[VALIDATE] Total validated URLs: {len(validated_urls)}")
        print(f"[VALIDATE] Returning top {len(top_validated_urls)} validated URLs")
        print(f"[VALIDATE] Insights: {self.insght} and Scope: {self.ppscope}")
        
        return top_validated_urls