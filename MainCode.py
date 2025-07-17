import os
import json
import re
import bs4
from pathlib import Path
from openai import OpenAI
from bs4 import BeautifulSoup
from datetime import datetime

import re

def clean_json_block(output):
    # Remove ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", output, re.DOTALL)
    if match:
        return match.group(1)
    return output.strip()


api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    api_key = api_key.strip()

client = OpenAI(api_key=api_key)
OUTPUT_BASE = Path("output_site")

PHASE1_PROMPT = """
Output only a JSON object with keys: niche, websiteFormat, keywords, keywordClusters, domainSuggestions. Do not add any text or explanation.
1. Randomly select 3 profitable niches from high-CPC industries

2. For each, simulate research from tools like:
   - Google Keyword Planner, Ubersuggest, Ahrefs, LowFruits.
   - BuzzSumo
3. Compare the 3 niches:
   - Estimated CPC ($/click)
   - Competition level (Low/Medium/High)
   - Long-tail keyword volume (good or poor)

4. Choose the best-performing niche based on:
   - High CPC
   - Low competition
   - Rich long-tail potential

5. For the chosen niche:
   - Generate 5–15 long-tail keywords with low difficulty and decent monthly volume.
   - Group keywords into 2–3 topical clusters (silos).

After choosing the niche:
Think of a couple high-performing, AdSense-eligible website **format** not just a blog but it can be a blog just make it random.
- Examples: Tools/calculators, interactive guides, comparison engine, AI-powered content generator, affiliate + content hybrid, etc. and pick at random one of the most profitable options, do not always pick affiliate links as the most profitable i do want to main type of income to ab adsense but affiliation is ok too.

- Propose 2–3 brandable, available-style domain names based on the niche and keyword intent.

Do not summarize or explain — just give me the output like you're building it into a project.
"""

def phase2_prompt(phase1_data):
    return f"""You are now executing **Phase 2: Website Generation (Frontend)**.

 FORMAT: {phase1_data.get("websiteFormat", "blog").title()}

 OBJECTIVE:
Build a fully finished, standalone, mobile-first website using **clean vanilla HTML/CSS/JS** or **React + TailwindCSS**, based on the format below.

 ALL OUTPUT MUST INCLUDE:
- Responsive layout with header, sticky navigation bar, and footer
- Image carousel (if applicable)
- Lazy-loaded and compressed image tags
- Insert 3 AdSense placeholders:
   <!-- ad:top -->, <!-- ad:middle -->, <!-- ad:bottom -->
- Google Analytics script (use placeholder GA_ID)
- Cookie consent banner (use JS or CDN like cookieconsent)
- All pages styled in a clean, modern, mobile-first UI

 REQUIRED PAGES:
- index.html (main page)
- about.html
- contact.html (with working form and client-side validation)
- privacy-policy.html
- terms-of-service.html

 LAYOUT PER FORMAT:
- Blog → Multiple article summaries, grid/list layout, clean content cards, natural ad breaks
- Tool → Input forms, results section, interactive UI
- Comparison → Feature tables, filters, and CTAs
Blog
Homepage: Grid or list of article summaries with featured images and short excerpts
Article Cards: Clean cards with title, thumbnail, meta (date, author), and read-more links
Article Pages:
Well-structured with H1 title, H2/H3 subheaders
Images with descriptive alt text, lazy-loaded
Natural ad breaks (e.g., after intro, mid-article, end) with placeholders like <!-- ad:top -->
Related articles or internal links at bottom to keep users browsing
Sidebar (optional): Popular posts, recent posts, categories, or tag clouds (good for SEO and ad slots)
Footer: Newsletter signup, contact info, social media links
News / Magazine
Homepage:
Multiple article categories (e.g., World, Tech, Sports) clearly separated
Featured slider/carousel at top with breaking news
Category Pages: Paginated lists of articles sorted by date or popularity
Article Pages:
Headlines, byline, date, image banners
Inline ads after key paragraphs
Social share buttons to increase reach
Sidebar Widgets:
Trending articles
Ad banners or ad placeholders
Newsletter signup
Footer: Links to sections, legal, contact, sponsors
Comparison
Landing Page:
Clear headline explaining comparison purpose
Interactive filters or dropdowns for user preferences (optional)
Comparison Tables:
Rows for features, columns for products/services
Clear "Best Choice" highlights or badges
Pricing info, star ratings, pros/cons columns
Call-to-Action (CTA) Buttons:
“Buy Now,” “Learn More,” or affiliate links prominently placed
Content Blocks:
Intro explaining methodology
Individual product reviews or summaries below tables
Ad Placement:
Ads near comparison tables and CTAs (high CTR spots)
Sidebar with related ads/products
How-To / Tutorial
Step-by-Step Sections:
Numbered or bullet steps with clear, concise instructions
Screenshots, images, or embedded videos for each step (lazy-loaded)
Intro and Conclusion: Summary of benefits and key takeaways
Code Blocks or Tips (if applicable): Highlighted for clarity
Ad Slots:
After intro paragraph
Mid-way through steps
End of tutorial, before related content
Sidebar or Related Posts: Links to similar tutorials for user retention
Tool (Interactive Apps)
Input Form:
Clear fields with labels and placeholders
Validation feedback on inputs (client-side JS)
Results Area:
Dynamically updated results, charts, or tables
Clear explanations of output
Instructions Section: How to use the tool and benefits
Ads:
Banner ads near form and results sections (high visibility)
Native-style ads integrated into UI but non-intrusive
Mobile Optimization: Buttons and inputs large enough for touch
Optional: Save/share results functionality (UI only)
Listicle (Top X Lists)
Intro Section:
Brief overview of list purpose and criteria
List Items:
Numbered items with title, thumbnail image, and short description
Each item separated visually with spacing or borders
Ad Breaks:
Insert ads after every 3-5 list items for good balance (e.g., <!-- ad:middle -->)
Summary or Conclusion: Final thoughts or recommendation
Sidebar or Related Lists: Other popular listicles to boost page views
 SEO:
- Title and meta tags
- Open Graph tags
- Canonical link
- Mobile-optimized viewport tag

 IMPORTANT:
Return output as a valid JSON object where:
- Keys = filenames (like 'index.html')
- Values = full HTML/JS/CSS content
- DO NOT include Markdown or commentary"""

def phase2_5_prompt(phase1_data):
    return f"""
You are now executing **Phase 2.5: Backend Generation**.
While executing keep in mind your responses need to be optimized and condensed so it does not crash the processes exceed the token limit and gives an actual result.
 Objective:
Build a complete backend for the frontend from Phase 2. Ensure it is:
- Compatible with the HTML/React site previously generated.
- Bug-free and ready to deploy.
- Modular and reusable across niches.

 Requirements:
- Use **Node.js + Express** or **Python (Flask)** (pick whichever fits better).
- Include routes for:
  - Contact form submission (from contact.html)
  - Serving blog posts (if needed)
  - Any dynamic interaction features
- Include minimal security (input validation, rate limiting if form)

 Output format:
Return **only a JSON object** where:
- Keys are file paths (e.g., `server.js`, `routes/contact.js`)
- Values are full code content
- No markdown, no comments, no extra explanation

  Example Output:
{{
  "server.js": "...",
  "routes/contact.js": "...",
  "package.json": "..."
}}

Do not include personal info or API keys.
Make sure JSON is valid."""

def phase3_prompt(phase1_data):
    return f"""
You are now executing **Phase 3: Content Generation** for format: {phase1_data.get("websiteFormat", "blog")}.

 OBJECTIVE:
For each selected long-tail keyword, write a fully original, AdSense-safe, SEO blog post between 700–1200 words.

 STRUCTURE:
- meta description
- H1 title
- H2/H3 subheaders
- Internal linking
- Relevant <img> tags with alt text (lazy-loaded)
- Include 3 ad placeholders:
   <!-- ad:top -->, <!-- ad:middle -->, <!-- ad:bottom -->

 LAYOUT PER FORMAT:
- Blog → Articles with introduction, body, images, and CTA
- Tool → Usage instructions, benefits, feature breakdown
- Comparison → Product comparisons, ranking tables, pros/cons blocks

 EXTRAS:
Also generate:
- about.html
- contact.html
- privacy-policy.html
- terms-of-service.html

 OUTPUT:
Return a single valid JSON object. Example:
{{
  "blog/solar-tax-breaks-2025.html": "<html>...</html>",
  "about.html": "<html>...</html>",
  "contact.html": "<html>...</html>",
  ...
}}

DO NOT include Markdown or smart quotes.
"""

def call_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert developer and SEO specialist."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3500,
        temperature=0.7,
    )
    return response.choices[0].message.content

    print(f"Saved {len(files)} files to {folder_path}")

def save_files_from_json(response_text, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f" Invalid JSON data:\n{e}")
        return

    for filename, content in data.items():
        file_path = Path(output_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Saved] {file_path}")



def generate_sitemap(base_url, output_folder):
    sitemap_path = Path(output_folder) / "sitemap.xml"
    urls = []

    for html_file in Path(output_folder).rglob("*.html"):
        rel_path = html_file.relative_to(output_folder).as_posix()
        url = f"{base_url}/{rel_path}"
        urls.append(url)

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap_content += f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{now}</lastmod>\n    <priority>0.80</priority>\n  </url>\n"
    sitemap_content += '</urlset>'

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    print(f" Sitemap saved to {sitemap_path}")


def validate_html_and_links(base_folder):
    print("\n🔍 Validating HTML structure and links...")
    html_files = list(Path(base_folder).rglob("*.html"))
    broken_links = []

    for html_file in html_files:
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            soup = BeautifulSoup(content, "html5lib")
            print(f" Valid HTML: {html_file}")
        except Exception as e:
            print(f" HTML Parse Error: {html_file} - {e}")

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("http") or href.startswith("#"):
                continue
            target_path = (html_file.parent / href).resolve()
            if not target_path.exists():
                broken_links.append((html_file, href))

    if broken_links:
        print("\n Broken links found:")
        for origin, missing in broken_links:
            print(f"- {origin} → {missing}")
    else:
        print(" No broken links found.")

def main():
    print("=== Phase 1: Niche & Keyword Discovery ===")
    phase1_raw = call_openai(PHASE1_PROMPT)
    cleaned_phase1 = clean_json_block(phase1_raw)

    try:
        phase1_data = json.loads(cleaned_phase1)
    except json.JSONDecodeError:
       print("Phase 1 output is not valid JSON. Raw output:\n", phase1_raw)
       return


    print("=== Phase 2: Frontend Generation ===")
    phase2_raw = call_openai(phase2_prompt(phase1_data))
    print("Phase 2 raw output:\n", phase2_raw)
    cleaned_phase2 = clean_json_block(phase2_raw)    # ADD THIS LINE
    save_files_from_json(cleaned_phase2, "phase2_frontend")   # USE cleaned_phase2 here instead of phase2_raw


    print("=== Phase 2.5: Backend Generation ===")
    phase2_5_raw = call_openai(phase2_5_prompt(phase1_data))
    save_files_from_json(phase2_5_raw, "phase2_5_backend")

    print("=== Phase 3: Content Generation ===")
    phase3_raw = call_openai(phase3_prompt(phase1_data))
    save_files_from_json(phase3_raw, "phase3_content")

    print("\n=== MANUAL STEPS ===")
    domain = phase1_data.get("domainSuggestions", ["N/A"])[0]
    print(f"1. Purchase domain: {domain}")
    print("2. Set up Google AdSense account.")
    print("3. Configure affiliate links if used.")
    print("====================\n")

    print("Website generation workflow completed.")

if __name__ == "__main__":
    main()
    import subprocess
    subprocess.run(["python", "deploy_to_github.py"])
