from openai import OpenAI
import json
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup


class ValidateURLs:
    def __init__(
        self, access_token: str, insight: str, pp_scope: str, max_results: int
    ):
        print("[INIT] Initializing ValidateURLs class...")
        self.access = access_token
        self.client = OpenAI(api_key=access_token)
        self.insght = insight
        self.ppscope = pp_scope
        self.max_results = max_results
        print("[INIT] ValidateURLs initialized successfully")
        self.SYSTEMPROMPTFORQUERY = """
You are a specialized AI agent designed to validate project insights and scope information by generating a targeted search query. Your primary objective is to verify the accuracy, completeness, and context of project information found in business intelligence data.

## Core Responsibilities

When provided with project data containing an insights_summary and pp_scope (project scope), you must generate exactly 1 strategic search query that will help validate the core project announcement.

## Query Generation Guidelines

### Project Verification Query
- Focus on verifying the core project announcement
- Include: company name, project type, location, and capacity/scale
- Format: "[Company Name] [Project Type] [Location] [Capacity] [Recent Year]"
- Example: "InSolare Energy BESS project Kolimigundla Andhra Pradesh 600 MW 2025"

## Search Query Best Practices

- Keep queries concise: 4-10 words optimal
- Use specific identifiers: company names, project locations, capacities
- Include temporal markers: year or "recent" for current projects
- Avoid special operators: no quotes, no "-" operators, no "site:" operators
- Focus on verifiable facts: numbers, names, locations, dates
- Prioritize official sources: government agencies, industry publications

## Output Format

Return ONLY a single string containing the search query (8-10 words maximum). Do not include any JSON, explanations, or additional formatting.

**Example output:**
```
InSolare Energy BESS project Kolimigundla Andhra Pradesh 600 MW 2025
```

## Critical Elements to Validate

### From insights_summary:
- Company names and their roles
- Project capacity/scale metrics
- Location specificity
- Project stage/status
- Market impact claims

### From pp_scope:
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

## Response Requirements

- Generate exactly 1 query as a single string
- Maximum 8-10 words
- Focus on the most critical verifiable elements
- Balance specificity with searchability
- Prioritize recent, verifiable information
- No additional text, formatting, or explanations

## Goal

Your goal is to enable efficient validation of project intelligence through a strategic, well-crafted search query that will return authoritative sources confirming or refuting the provided information.
"""

        self.SYSTEMPROMPTVALIDATOR = """
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

    def search_links(self, query: str, max_results: int, timelimit: str = "y"):
        print(
            f"[SEARCH] Searching for query: '{query}' (max_results={max_results}, timelimit={timelimit})"
        )
        try:
            results = DDGS().text(
                query,
                region="wt-wt",
                safesearch="off",
                timelimit=timelimit,
                max_results=max_results,
            )

            # Extract only the hrefs and filter out wikipedia.com
            links = [
                result["href"]
                for result in results
                if "wikipedia.com" not in result["href"]
            ]
            print(f"[SEARCH] Links: {links}")

            return {
                "success": True,
                "query": query,
                "total_results": len(links),
                "links": links,
            }
        except Exception as e:
            print(f"[SEARCH] Error during search: {str(e)}")
            return {"errored": str(e)}

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

    def validate(self, max_retries: int = 3):
        print(f"[VALIDATE] Starting validation process with max_retries={max_retries}")
        validated_urls = []
        seen_urls = set()  # Track all URLs we've already seen across retries
        
        retry_count = 0
        
        while retry_count < max_retries:
            print(f"\n[VALIDATE] ===== Retry {retry_count + 1}/{max_retries} =====")
            
            # Increase max_results for DDG search with each retry
            # Start with 50, then 75, then 100, etc.
            current_search_limit = 50 + (retry_count * 25)
            print(f"[VALIDATE] Current DDG search limit: {current_search_limit}")
            
            queries = self.generateSearchQueries()
            print(f"[VALIDATE] Processing {len(queries)} generated queries...")

            for idx, query in enumerate(queries, 1):
                if len(validated_urls) >= self.max_results:
                    print(f"[VALIDATE] Reached target of {self.max_results} validated URLs, stopping search")
                    break
                    
                print(f"\n[VALIDATE] Processing query {idx}/{len(queries)}: '{query}'")
                unvalidated_urls = self.search_links(
                    query=query, max_results=current_search_limit
                )
                print(f"[VALIDATE] Search results: {unvalidated_urls}")

                if unvalidated_urls.get("success"):
                    links = unvalidated_urls.get("links", [])
                    
                    # Filter out already seen URLs
                    new_links = [url for url in links if url not in seen_urls]
                    print(f"[VALIDATE] Found {len(links)} URLs, {len(new_links)} are new (not seen before)")
                    
                    # Add new links to seen set
                    seen_urls.update(new_links)
                    
                    print(f"[VALIDATE] Validating {len(new_links)} new URLs...")

                    for url_idx, url in enumerate(new_links, 1):
                        if len(validated_urls) >= self.max_results:
                            print(f"[VALIDATE] Reached target of {self.max_results} validated URLs, stopping validation")
                            break
                            
                        print(f"[VALIDATE] Processing URL {url_idx}/{len(new_links)}: {url}")
                        html_content = self.getHTML(website=url)
                        if html_content.get("response_code") == 200:
                            try:
                                validation_result = self.validateHTML(
                                    content=html_content.get("content")
                                )
                                matches = validation_result.get("matches", False)

                                # Collect all URLs that match
                                if matches:
                                    print(
                                        "[VALIDATE] URL validated successfully - content matches"
                                    )
                                    validated_urls.append(url)
                                else:
                                    print(
                                        "[VALIDATE] URL does not match - content does not align"
                                    )
                            except Exception as e:
                                print(
                                    f"[VALIDATE] Error during validation of URL: {str(e)}"
                                )
                                continue
                        else:
                            print(
                                f"[VALIDATE] Skipping URL due to non-200 response code: {html_content.get('response_code')}"
                            )
                else:
                    print(
                        f"[VALIDATE] Search failed with error: {unvalidated_urls.get('errored', 'Unknown error')}"
                    )
            
            # Check if we have enough validated URLs
            if len(validated_urls) >= self.max_results:
                print(f"[VALIDATE] Successfully found {self.max_results} validated URLs")
                break
            elif len(validated_urls) > 0:
                print(f"[VALIDATE] Found {len(validated_urls)} validated URLs, stopping retries")
                break
            else:
                print(f"[VALIDATE] No validated URLs found yet ({len(validated_urls)}/{self.max_results})")
                retry_count += 1
                if retry_count < max_retries:
                    print("[VALIDATE] Will retry with increased search limit...")
                else:
                    print("[VALIDATE] Max retries reached, stopping")

        # Keep only the first self.max_results validated URLs
        if len(validated_urls) > self.max_results:
            top_validated_urls = validated_urls[: self.max_results]
        else:
            top_validated_urls = validated_urls

        print("\n[VALIDATE] Validation process completed")
        print(f"[VALIDATE] Total validated URLs: {len(validated_urls)}")
        print(f"[VALIDATE] Total URLs seen across all retries: {len(seen_urls)}")
        print(f"[VALIDATE] Returning top {len(top_validated_urls)} validated URLs")
        print(f"[VALIDATE] Insights: {self.insght} and Scope: {self.ppscope}")

        return top_validated_urls
