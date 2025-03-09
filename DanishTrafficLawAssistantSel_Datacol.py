from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time




# Links to Scrape
laws_to_scrape = [
    {"name": "Færdselsloven_2024", "url": "https://www.retsinformation.dk/eli/lta/2024/1312"}
]

# Setup Selenium webdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(options=chrome_options)

all_laws = {}

for law in laws_to_scrape:
    print(f"Scraping: {law['name']}...")

    # Load the page
    driver.get(law["url"])
    time.sleep(5)  #Delay for JavaScript to render

    # Parse the page
    soup = BeautifulSoup(driver.page_source, "html.parser")

    laws = []
    current_chapter = None  # Track the current chapter
    current_law = None  # Track the current law paragraph
    current_condition = None  # Track the current numbered condition
    inside_stk = False  # Track if we're inside a Stk.
    inside_definitions = False  # Track if we are inside the definition list (Chapter 2)

    for tag in soup.find_all("p"):

        #Chapter detection
        if "ParagrafGruppeOverskrift" in tag.get("class", []):
            current_chapter = tag.text.strip()
            inside_definitions = False  # Reset definition tracking
            continue

        #Law Paragraph detection
        if "Paragraf" in tag.get("class", []):
            paragraph_number = tag.find("span", class_="ParagrafNr")
            if paragraph_number:
                current_law = {
                    "chapter": current_chapter,
                    "paragraph": paragraph_number.text.strip(),
                    "text": tag.text.strip().replace(paragraph_number.text.strip(), "").strip(),
                    "subsections": [],  # Store subsections here when no ListeNr is present
                    "conditions": [],
                    "definitions": []  # For Chapter 2 definitions
                }
                laws.append(current_law)
                current_condition = None  # Reset condition tracking
                inside_stk = False  # Reset stk tracking
            continue

        #Detect Stk. subsection
        if any(cls.startswith("Stk") for cls in tag.get("class", [])):
            subsection_text = tag.text.strip()
            subsection_number = subsection_text.split(".")[0].replace("Stk", "").strip()

            try:
                subsection_number = int(subsection_number) if subsection_number.isdigit() else None
            except ValueError:
                subsection_number = None  # None if invalid

            current_stk = {
                "text": subsection_text,
                "conditions": []
            }

            # If there are no numbered conditions yet, attach Stk. to the main paragraph
            if not current_law["conditions"]:
                current_law["subsections"].append(current_stk)
            else:
                # else, attach Stk. to the last numbered condition
                if current_condition:
                    current_condition["subsections"].append(current_stk)

            inside_stk = True  # is inside Stk.
            continue

        #Conditions (numbered items, Liste1)
        if "Liste1" in tag.get("class", []):
            if current_law:
                # If inside a Stk. close it before adding a new numbered condition
                inside_stk = False

                condition = {
                    "number": len(current_law["conditions"]) + 1,
                    "text": tag.text.strip(),
                    "subsections": []
                }

                current_law["conditions"].append(condition)
                current_condition = condition
            continue

        # Detect definitions (TekstGenerel) → Only for chapter 2
        if "TekstGenerel" in tag.get("class", []):
            if current_law:
                definition_text = tag.text.strip()

                # Check if it's a new definition (it starts with a number)
                if definition_text[0].isdigit():
                    current_law["definitions"].append({
                        "term": definition_text,  # Store the definition title
                        "description": ""
                    })
                    inside_definitions = True  # Inside a definition
                elif inside_definitions and current_law["definitions"]:
                    # Append to the last definition as description
                    current_law["definitions"][-1]["description"] += " " + definition_text

            continue

    all_laws[law["name"]] = laws
    print(f"Finished scraping {law['name']}")

# Close the browser
driver.quit()

# Save to JSON
with open("danish_traffic_laws_2024.json", "w", encoding="utf-8") as f:
    json.dump(all_laws, f, indent=4, ensure_ascii=False)

print("Saved to danish_traffic_laws_2024.json")
