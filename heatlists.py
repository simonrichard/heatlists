import re
import requests

from bs4 import BeautifulSoup
from pymongo import MongoClient

URL = "http://dynadf.ca/LeChicDeLaDanse/lechic2016_HeatLists.htm"

D_ID = "TABLE_CODE_(\d+)"
P_NAME = "With (.+)"
D_ID, P_NAME = (re.compile(x) for x in (D_ID, P_NAME))

DTABLE = MongoClient().heatlists.dancers


def scrape(url=URL):

    DTABLE.drop()

    soup = BeautifulSoup(requests.get(url).text, "lxml")

    for d_name, d_id in soup.find("table").select("tr"):
        d_name = d_name.text
        d_id, = D_ID.findall(d_id.input["onclick"])
        DTABLE.save({"name": d_name, "_id": d_id})

    for entries in soup.select("div[id^=TABLE_CODE]"):

        d_id, = D_ID.findall(entries["id"])

        for partner in entries.select("strong")[1:]:
            if partner.text == "With ":
                continue

            p_id = DTABLE.find_one({"name":
                P_NAME.search(partner.text).group(1)})["_id"]
            DTABLE.update({"_id": d_id}, {"$push": {"partners": p_id}})

            for event in partner.find_next("table").select("tr")[1:]:
                _, _, heat, title = event.select("td")
                heat = "%s: %s" % (heat.text, title.text)
                for _id in [d_id, p_id]:
                    DTABLE.update({"_id": _id}, {"$push": {"heats": heat}})


def get_heats(name):

    def normalize(s):
        return " ".join(reversed(s.split(", ")))

    if not DTABLE.count():
        scrape()

    for heat in set(DTABLE.find_one({"name": name})["heats"]):
        competitors = []
        for competitor in DTABLE.find({"heats": {"$in": [heat]}}):
            partner = DTABLE.find_one({
                "_id": {"$in": competitor["partners"]},
                    "heats": heat})
            competitors.append([competitor["name"], partner["name"]])
        competitors = [list(x) for x in set(map(frozenset, competitors))]

        print("\n" + heat)
        print("===========================")
        for couple in competitors:
            print(" & ".join(map(normalize, couple)))
        print()
