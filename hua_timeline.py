import os
import re
import bs4
import json
import pymods
import requests
import datetime
import dateparser


def img_lookup(pid):
    """Query for object type and return correct JPG location"""
    r = requests.get("https://fsu.digital.flvc.org/islandora/object/{0}/datastream/JPG/view".format(pid))
    if r.status_code == 200:
        return r.url
    elif r.status_code == 404:
        r2 = requests.get("https://fsu.digital.flvc.org/islandora/object/{0}/pages".format(pid))
        soup = bs4.BeautifulSoup(r2.text, 'lxml')
        div = soup.find_all('div', class_="islandora-objects-grid-item")[0]
        dd = div.find('dd')
        a = dd.find('a')
        if a is not None:
            return "https://fsu.digital.flvc.org{0}/datastream/JPG/view".format(a['href'])
        else:
            return None
    else:
        return None


tl = {'scale': 'human',
      "title": {"media": {"caption": "",
                          "credit": "",
                          "url": "http://myweb.fsu.edu/mmiguez/timeline/assets/images/heritageprotocol-graphic2.jpg",
                          "thumb": 	""},
                "text": {"headline": "Welcome to the Heritage & University Archives Timeline",
                         "text": "<p>This interactive timeline highlights a curated collection of Florida State University's history.</p><p>Click on the arrow to the right to learn more.</p>"}},}
events = []
tl.update(events=events)

for item in os.listdir('MODS'):
    ev = next(pymods.MODSReader(os.path.join('MODS/', item)))  # really need to fix this in pymods

    # Unique ID
    if ev.pid:
        event = {'unique_id': ev.pid}
    else:
        #print(item)
        continue

    # Text
    if ev.abstract:
        text = {'headline': ev.titles[0], 'text': ev.abstract[0].text}
    else:
        text = {'headline': ev.titles[0]}
    event['text'] = text

    # Date
    display_date = ev.dates[0].text
    if 'circa' in display_date:
        date = display_date.strip('circa')
    else:
        date = display_date
    if ' - ' in date:
        event['start_date'] = {"display_date": display_date,
                               "year": date[0:4]}
        event['end_date'] = {"display_date": display_date,
                             "year": date[-4:]}
    else:
        try:
            date = dateparser.parse(date)
            event['start_date'] = {"display_date": display_date}
            if date.year > 0:
                event['start_date'].update(year=str(date.year))
            else:
                continue
            if date.month > 0:
                event['start_date'].update(month=str(date.month))
            if date.day > 0:
                event['start_date'].update(day=str(date.day))
        except AttributeError:
            try:
                date = re.sub('[A-Za-z]', '', display_date).split('-')[0]
                date = dateparser.parse(date)
                event['start_date'] = { "display_date": display_date }
                if date.year > 0:
                    event['start_date'].update(year=str(date.year))
                else:
                    continue
                if date.month > 0:
                    event['start_date'].update(month=str(date.month))
                if date.day > 0:
                    event['start_date'].update(day=str(date.day))
            except AttributeError:
                print(item, date, display_date)
                continue

    # Group
    if int(event['start_date']['year']) < 1949:
        event['group'] = 'FSCW'
    else:
        event['group'] = 'FSU'

    # Media
    media = {'credit': ev.purl[0], 'link': ev.purl[0]}
    url = img_lookup(ev.pid)
    tn = "https://fsu.digital.flvc.org/islandora/object/{0}/datastream/TN/view".format(ev.pid)
    media.update(thumbnail=tn, url=url)
    event.update(media=media)


    tl['events'].append(event)

with open('hua-{0}.json'.format(datetime.date.today()), 'w') as f:
    f.write(json.dumps(tl, indent=2))
