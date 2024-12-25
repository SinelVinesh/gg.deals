import random
import time

from bs4 import BeautifulSoup
import json
import requests

workingShop = ["GAMIVO", "Eneba", "Kinguin", "G2A", "CDKeys.com", "Yuplay"]


class GamePrice:
    def __init__(self, shop, price):
        self.shop = shop
        self.price = price
        self.working = self.shop in workingShop


class Game:
    def __init__(self, game_id, name, detail_link, prices):
        self.game_id = game_id
        self.name = name
        self.detail_link = detail_link
        self.prices = prices

    def add_price(self, shop, price):
        self.prices.append(GamePrice(shop, price))

    def get_best_price(self):
        game_price = {}
        best_price = 1000000
        for price in self.prices:
            if price.price < best_price and price.working:
                game_price = price
        return game_price

    def __str__(self):
        representation = f"{self.name}\n"
        best_price = self.get_best_price()
        representation += f"Best Working Price: {best_price.price} at {best_price.shop}\n"
        representation += "Prices:\n"
        for price in self.prices:
            representation += f"[{"OK" if price.working else "NOK"}] {price.shop}: {price.price}\n"
        return representation


class GameEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Game):
            return obj.__dict__
        return super().default(obj)


def get_soup(link):
    req = requests.get(link)
    html = req.content
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_soup_headers(link, headers):
    req = requests.get(link, headers=headers)
    html = req.content
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_page_games(link):
    soup = get_soup(link)
    games = []
    game_divs = soup.findAll("div", {"data-container-game-id": True})
    for game_div in game_divs:
        game_id = game_div["data-container-game-id"]
        game_link = f"https://gg.deals/us{game_div.find("a")["href"]}"
        game_name = game_div.find("a", {"class": "title-inner"}).text
        game = Game(game_id, game_name, game_link, [])
        games.append(game)
    return games


def get_price(game: Game):
    link = game.detail_link
    headers = {"X-Requested-With": "XMLHttpRequest"}
    soup = get_soup_headers(link, headers=headers)
    keyshops = soup.findAll("div", {"data-shop-name": True})
    prices = []
    for keyshop in keyshops:
        shop = keyshop["data-shop-name"]
        price = float(keyshop["data-deal-value"])
        prices.append(GamePrice(shop, price))
    return prices


def get_games():
    games = {"games": []}
    for i in range(1, 2):
        link = f"https://gg.deals/games/?page=${i}"
        games["games"].extend(get_page_games(link))
        time.sleep(random.randint(1, 3) / 2)

    export_games(games)


def get_prices():
    games = []
    with open("games.json") as f:
        games_raw = json.load(f)["games"]

    for game_raw in games_raw:
        try:
            game = Game(game_raw["game_id"], game_raw["name"], game_raw["detail_link"], [])
            game.prices = get_price(game)
            games.append(game)
            print(game)
        except Exception as e:
            print(e)
        time.sleep(random.randint(1, 3) / 2)
    export_games(games_raw)


def export_games(games):
    with open("games.json", "w") as f:
        json.dump(games, f, cls=GameEncoder)


def driver():
    get_games()
    get_prices()
