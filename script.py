import requests
from bs4 import BeautifulSoup
import re

# url = 'https://www.psoas.fi/en/apartments'
url = 'https://www.psoas.fi/en/apartments/?_sfm_htyyppi=p&_sfm_huoneistojen_tilanne=vapaa_ja_vapautumassa&_sfm_koko=7+84&_sfm_vuokra=161+761&_sfm_huonelkm=1+7#'
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
container_div = soup.find("div", class_="huoneistohaku__lista__container")
updates = []

if container_div:
    apartment_divs = container_div.find_all("article", class_="card-huoneisto")

    for apartment_div in apartment_divs:
        title = apartment_div.find("span", class_="card-huoneisto__summary__nimi").text.strip()
        address = apartment_div.find("span", class_="card-huoneisto__summary__osoite").text.strip()
        descr = apartment_div.find('span', class_ = 'card-huoneisto__summary__report').text.strip()

        span_element = apartment_div.find("span", class_="card-huoneisto__summary__nimi")
        link = span_element.find("span").get("onclick")
        if link:
            # Extracting the URL from the onclick attribute
            url = re.search(r"\('([^']+)', '_self'\);", link)
            if url:
                url = url.group(1)

        print(f"Title: {title}")
        print(f"Address: {address}")
        print(f'Description: {descr}')
        print(f"Link: {url}")
        print("----------")
        updates.append(f"{title}\n{address}\n{descr}\n{url}")
