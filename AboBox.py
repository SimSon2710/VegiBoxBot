from Ingredient import Ingredient
from typing import List
from datetime import date
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import logging


class AboBox:
    logger = logging.getLogger(__name__)

    boxes_lst: List[super] = []

    def __init__(self, name: str, week: int, ingredients: List[Ingredient], size: str = "", url: str = ""):
        self.name = name
        self.week: int = week
        self.url: str = url
        self.size: str = size
        self.ingredients: List[Ingredient] = ingredients

        if not self in AboBox.boxes_lst:
            AboBox.boxes_lst.append(self)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, AboBox):
            return NotImplemented
        return self.name == o.name and self.week == o.week and self.size == o.size

    def __str__(self) -> str:
        return f"{self.name}, KW {self.week}: {self.ingredients}"

    @classmethod
    def get_abo_details(cls, week: str, box_name: str, box_size: str) -> str:
        calendar_wk = date.isocalendar(date.today())[1]
        text = ""
        box_name = box_name.lower()
        box_size = box_size.lower()

        if week == 'naechste_woche':
            calendar_wk += 1

        for abo in cls.boxes_lst:
            if box_name in abo.name.lower() and box_size.lower() in abo.size.lower() and calendar_wk == abo.week:
                if abo.ingredients:
                    text = f'<b>Kalenderwoche {abo.week}</b> ({abo.name}):\n\n'
                    for ing in abo.ingredients:
                        try:
                            text += f'<a href="{ing.recipes_url}">{ing.name}</a>\n'
                        except AttributeError:
                            text += f'{ing.name}\n'
                    text += f'\n<a href="{abo.url}">Zu den Boxen</a>'
                else:
                    text = f"Für die {abo.name} gibt es noch keine Angaben für die {abo.week}. Kalenderwoche."
        if not text:
            text = f"Leide ergab die Suche nach deiner Kiste keinen Treffer. Probier es z. B. mit \"/{week} mix " \
                   f"mittel\" "
        return text

    # your method to scrape the products and pipe them to e.g. AboBox
    @classmethod
    def get_all_boxes(cls) -> None:
        cookies = {'cb-enabled': 'accepted'}
        headers = {'User-Agent': 'Mozilla/5.0'}

        year = date.today().year
        calender_wks = [
            date.isocalendar(date.today())[1],
            date.isocalendar(date.today())[1] + 1
        ]
        for calender_wk in calender_wks:
            urls = {
                "klein": f"https://...{year}...{calender_wk}",
                "mittel": f"https://...{year}...{calender_wk}",
                "gross": f"https://...{year}...{calender_wk}"
            }
            for size_url in urls:
                url = urls[size_url]
                try:
                    page = requests.get(url=url, headers=headers, cookies=cookies)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    boxes = soup.find_all('div', class_=["aufzaehlung04 odd", "aufzaehlung04"])
                except RequestException as e:
                    cls.logger.error("%s", repr(e))
                    continue
                for box in boxes:
                    ingredients_lst = []
                    box_name = box.find('p').text
                    box_ingredients = [x.text for x in box.findAll('nobr')]
                    box_ingredients_a_tag = [x.text for x in box.find_all('a')]
                    box_ingredients_wo_url = list(set(box_ingredients).difference(set(box_ingredients_a_tag)))
                    box_ingredients_recipes = [x['href'] for x in box.find_all('a', href=True)]
                    for ing, rec in zip(box_ingredients_a_tag, box_ingredients_recipes):
                        ingredients_lst.append(Ingredient(name=ing, recipes_url=rec))
                    for ing in box_ingredients_wo_url:
                        if ing:
                            ingredients_lst.append(Ingredient(name=ing))
                    AboBox(
                        name=box_name,
                        url=url,
                        week=calender_wk,
                        ingredients=ingredients_lst,
                        size=size_url if box_name.split()[-1] in "kleinmittelgroß" else ""
                    )
        cls.logger.info('Scraped abos from urls.')


if __name__ == '__main__':
    pass
