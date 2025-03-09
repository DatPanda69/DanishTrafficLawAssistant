# DanishTrafficLawAssistant
An AI assistent to help navigate the intricate traffic laws in Denmark


DISCLAIMER: This is not to be used as actual advice and should always be dobbel checked for any mistakes the AI may make


I used Selenium and BeautifulSoup for webscraping "Bekendtgørelse af færdselsloven" directly from "https://www.retsinformation.dk".

Then with the use of RAG(Retrieval-Augmented Generation) for navigating the dataset of "Færdselsloven" and give back the most fitting results compared to the question.

And then to make it more human-like and more readable i use openai to interpret the laws RAG return and explain it in a easy to understand way
