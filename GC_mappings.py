#!/usr/local/bin/python3
from html.parser import HTMLParser
import requests, json
from bs4 import BeautifulSoup, UnicodeDammit

def process_urls(capability_name, capability_cd_title, capability_elaboration_title):
  print('Connecting to AC website...')
  baseurl = 'https://www.australiancurriculum.edu.au/f-10-curriculum/curriculum-filter/?'
  params = {'subject' : [
              '11568', # English
              '11750', # Maths
              '11999', # Science
              '12095', # HASS
              '12317', # History
              '12376', # Geography
              '12493', # Civics
              '12556', # Economics
              '12718', # Dance
              '12727', # Drama
              '12736', # Media Arts
              '12745', # Music
              '12754', # Visual Arts
              '12972', # Design & Tech
              '12982', # Digital Tech
              '12992', # Health & PE
              # '13288', # Arabic
              '13311', # Auslan
              '13491', # Chinese
              '13528', # ATSI
              '13541', # Classical Greek
              '13545', # Classical Latin
              '13602', # French
              '13614', # German
              '13626', # Hindi
              '13638', # Indonesian
              '13650', # Italian
              # '13662', # Japanese
              '13674', # Korean
              # '13686', # Modern Greek
              '13698', # Spanish
              '13710', # Turkish
              '13722', # Vietnamese
              '13733', # Work Studies
              ],
            'year': [
              'Foundation+Year',
              'Year+1',
              'Year+2',
              'Year+3',
              'Year+4',
              'Year+5',
              'Year+6',
              'Year+7',
              'Year+8',
              'Year+9',
              'Year+10',
              'Year+10A',
              'Options',
              ],
            }
  for year in params['year']:
    url = baseurl + 'subject=' + '&subject='.join(params['subject'])+'&year='+year+'&capability='+capability_name
    print('Getting', url)
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    parse_html(soup, capability_cd_title, capability_elaboration_title)

def parse_html(html, capability_cd_title, capability_elaboration_title):
  global results

  # prepare relevant page sections
  # clear these, just in case of empty results carrying over
  cd_items = None
  elaboration_items = None
  cd_items = html.find_all('li',attrs={'title': capability_cd_title})
  elaboration_items = html.find_all('li',attrs={'title': capability_elaboration_title})

  # deal with multiple pages
  next_page = None
  pagination = html.find('div',attrs={'class': 'pager'})
  if pagination:
    link_element = pagination.find('a',attrs={'rel':'next'})
    if link_element:
      next_page = link_element['href']

  # content descriptions
  for cd in cd_items:
    # go to CD itself
    cd = cd.find_parent('section', attrs={'class' :'content-description'})
    # get CD ID and text, learning area and year
    cd_id = cd['id']
    cd_text = cd.contents[1].get_text().strip().split('\r\n')[0]
    # this breaks on some subjects that use non-latin encoding
    # It appears the DOM, although it looks ok, isn't constructed such
    # that any section tags are found above the CD tag in the heirarchy
    page_sections = cd.find_parents('section')
    learning_area = None
    for section in page_sections:
      learning_area = section.find('h2')
      if learning_area is not None:
        break
    learning_area = learning_area.contents
    if len(learning_area) > 1:
      year = learning_area[0].strip()
      learning_area = learning_area[2].strip()
    if learning_area not in results:
      results[learning_area] = {}
    if year not in results[learning_area]:
      results[learning_area][year] = {}
    results[learning_area][year][cd_id] = {
      'text': cd_text,
      'elements': {},
      'elaborations': {},
    }
    # find the GC div - need to restrict search space to avoid elaborations
    cd_footer = cd.footer.find_all('div', recursive=False)
    for capability in cd_footer:
      capability_div = capability.find(attrs={'class': 'capability-title'},string=capability_elaboration_title)
      if capability_div is not None:
        break
    # extract GC aspects for CD (if they exist)
    if capability_div:
      capability_elements = capability_div.parent.find_all('ul')
      for element in capability_elements:
        element_title = element.previous_sibling.previous_sibling.string.strip()
        element_aspects = [e.string for e in element.find_all('li', recursive=False)]
        results[learning_area][year][cd_id]['elements'][element_title] = element_aspects

  # elaborations
  for elaboration in elaboration_items:
    # link elaboration to CD
    elaboration_li = elaboration.parent.parent
    elaboration_id = elaboration_li['id']
    cd_id = elaboration_li.find_parent('section', class_='content-description')['id']
    page_sections = elaboration_li.find_parents('section')
    learning_area = None
    for section in page_sections:
      learning_area = section.find('h2')
      if learning_area is not None:
        break
    learning_area = learning_area.contents
    if len(learning_area) > 1:
      year = learning_area[0].strip()
      learning_area = learning_area[2].strip()
    if learning_area not in results:
      results[learning_area] = {}
    if year not in results[learning_area]:
      results[learning_area][year] = {}
    if cd_id not in results[learning_area][year]:
      cd_text = elaboration_li.parent.parent.parent.contents[1].get_text().strip().split('\r\n')[0]
      results[learning_area][year][cd_id] = {
        'text': cd_text,
        'elements': {},
        'elaborations': {},
      }
    elaboration_text = elaboration_li.contents[0].string.strip()
    # if there was a p tag in there, it's in a slightly different place
    if elaboration_text == "":
      elaboration_text = elaboration_li.find('p').get_text().strip()
    results[learning_area][year][cd_id]['elaborations'][elaboration_id] = {
      'text': elaboration_text,
      'elements': {},
    }
    # extract GC aspects for elaboration
    capability_div = elaboration_li.find(attrs={'class': 'capability-title'},string=capability_elaboration_title)
    capability_elements = capability_div.parent.find_all('ul')
    for element in capability_elements:
      element_title = element.previous_sibling.previous_sibling.string.strip()
      element_aspects = [e.string for e in element.find_all('li', recursive=False)]
      results[learning_area][year][cd_id]['elaborations'][elaboration_id]['elements'][element_title] = element_aspects

  # check if another page exists
  if next_page:
    print('Getting', next_page)
    r = requests.get(next_page, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    parse_html(soup, capability_cd_title, capability_elaboration_title)

headers = {
  'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

capability_list = {
  'literacy': ['Literacy','literacy','Literacy'],
  'numeracy': ['Numeracy','numeracy','Numeracy'],
  'ict': ['Information+and+Communication+Technology+%28ICT%29+Capability', 'information-communication','Information and Communication Technology (ICT) Capability'],
  'cct': ['Critical+and+Creative+Thinking','critical-creative','Critical and Creative Thinking'],
  'psc': ['Personal+and+Social+Capability','personal-social','Personal and Social Capability'],
  'ethical': ['Ethical+Understanding','ethical-understanding','Ethical Understanding'],
  'intercultural': ['Intercultural+Understanding','intercultural-understanding','Intercultural Understanding'],
}

# process data
for capability_name in capability_list:
  results = {}
  process_urls(*capability_list[capability_name])

  with open(capability_name+'_GC_mappings.json', 'w') as f:
    f.write(json.dumps(results,indent=2))