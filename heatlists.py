import argparse
import re
import requests

from bs4 import BeautifulSoup
from collections import defaultdict


def get_heats(url):
    couples_per_heat = defaultdict(list)
    heats_per_dancer = defaultdict(list)

    soup = BeautifulSoup(requests.get(url).text, "lxml")
    for dancer in soup.find_all("div", {"id": re.compile("TABLE_CODE_\d+")}):
        dancer_name = re.sub("Entries for ", "", dancer.find("strong").text)

        for partner in dancer.find_all("strong")[1:]:
            partner_name = re.sub("With ", "", partner.text)
            if dancer_name > partner_name:
                continue
            couple = (dancer_name, partner_name)

            heats = partner.find_next("table")
            for heat in heats.find_all("tr")[1:]:
                heat_data = [td.text for td in heat.find_all("td")]
                heat_number, heat_name = heat_data[2:4]
                heat_name = re.sub(" \([^)]+\)", "", heat_name)
                couples_per_heat[(heat_number, heat_name)].append(couple)

    for heat, couples in couples_per_heat.items():
        for couple in couples:
            for dancer in couple:
                heats_per_dancer[dancer].append(heat)

    return heats_per_dancer, couples_per_heat


def normalize(name):
    return " ".join(filter(None, name.split(", ")[::-1]))


def main(url, name):
    heats_per_dancer, couples_per_heat = get_heats(url)

    if name in heats_per_dancer:
        for heat in sorted(heats_per_dancer[name]):
            description = "%s: %s" % tuple(heat)
            print(description)
            print("=" * len(description))

            for couple in couples_per_heat[heat]:
                print(" & ".join(map(normalize, couple)))
            print()
    else:
        print("Couldn't find dancer %s. Try a different spelling." % name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Heatlists URL")
    parser.add_argument("--name", required=True,
                        help="Lastname, Firstname in quotes (e.g. 'Bizokas, Arunas')")

    args = parser.parse_args()
    main(args.url, args.name)
