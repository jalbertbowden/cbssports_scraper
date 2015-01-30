#!/usr/bin/env python

import re
import os
import sys
import django
import datetime
import argparse
import urlparse
import mechanize

from bs4 import BeautifulSoup

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), 'scraper/')))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), 'scraper/scraper/')))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from cbssports_scraper.models import *

TEAMS = {
    'GS': ''
}

class CbsSportsScraper(object):
    def __init__(self):
        self.cnt = 30
        self.url = "http://www.cbssports.com/nba/playerrankings"
        self.br = mechanize.Browser()
        self.positions = ['PG', 'SG', 'SF', 'PF', 'C' ]

    def scrape_position_links(self):
        self.br.open(self.url)

        for p in self.positions:
            s = BeautifulSoup(self.br.response().read())
            a = s.find('a', text=p)
            u = urlparse.urljoin(self.br.geturl(), a['href'])
            
            pos = Position()
            pos.name = p
            pos.url = u
            pos.save()

    def scrape_player_stats(self, player):        
        self.br.oepn(player.url)

        s = BeautifulSoup(self.br.response().read())
        f = lambda x: x.name == 'dt' and x.text == 'Birthdate:'

        dt = s.find(f)
        dd = dt.findNext('dd')

        (m,d,y) = dd.text.split('/')

        player.birthdate = datetime.date(int(m), int(d), int(y))

        f = lambda x: x.name == 'dt' and x.text == 'Team:'

        dt = s.find(f)
        dd = dt.findNext('dd')

        player.team_name = dd.text.strip()
        player.save()

    def scrape_players_for_position(self, position):
        self.br.open(position.url)        
        
        s = BeautifulSoup(self.br.response().read())
        r = re.compile('^/nba/players/playerpage/\d+$')
        
        for pa in s.findAll('a', href=r)[:self.cnt]:
            td = pa.findParent('td')
            ta = td.findAll('a')[-1]

            team_url = urlparse.urljoin(self.br.geturl(), ta['href'])
            player_url = urlparse.urljoin(self.br.geturl(), pa['href'])

            player = Player(position=position)
            player.name = pa.text.strip()
            player.url = player_url
            player.team_code = ta.text.strip()
            player.team_url = team_url
            player.save()

    def scrape(self):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scrape", help="do a fresh scrape of the top 30 players for positions PG/SG/SF/PF/C",
                        action="store_true")
    parser.add_argument("-e", "--export", help="export results as CSV",
                        action="store_true")
    args = parser.parse_args()

    scraper = CbsSportsScraper()
    scraper.scrape()