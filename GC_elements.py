#!/usr/local/bin/python3
from html.parser import HTMLParser
import requests, json
from bs4 import BeautifulSoup, UnicodeDammit

def process_urls(capability_name, capability_elements):
  print('Connecting to AC website...')
  baseurl = f'https://www.australiancurriculum.edu.au/f-10-curriculum/general-capabilities/{capability_name}/learning-continuum/?'
  params = {'level': [
              'Level+1',
              'Level+1a',
              'Level+1b',
              'Level+2',
              'Level+3',
              'Level+4',
              'Level+5',
              'Level+6',
              ],
            }
  for level in params['level']:
    url = baseurl + 'element=' + '&element='.join(capability_elements) + '&level=' + '&level='.join(params['level'])
    print('Getting', url)
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    parse_html(soup)

def parse_html(html):
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
    results[learning_area][year][cd_id]['elaborations'][elaboration_id] = {
      'text': elaboration_li.contents[0].string.strip(),
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
    parse_html(soup)

headers = {
  'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

capability_elements = {
  'literacy': ['Comprehending+texts+through+listening%2C+reading+and+viewing','Composing+texts+through+speaking%2C+writing+and+creating','Text+knowledge','Grammar+knowledge','Word+Knowledge','Visual+Knowledge'],
  'numeracy': ['Estimating+and+calculating+with+whole+numbers','Recognising+and+using+patterns+and+relationships','Using+fractions%2C+decimals%2C+percentages%2C+ratios+and+rates','Using+spatial+reasoning','Interpreting+statistical+information','Using+measurement'],
  'information-and-communication-technology-ict-capability': ['Applying+social+and+ethical+protocols+and+practices+when+using+ICT','Investigating+with+ICT','Creating+with+ICT','Communicating+with+ICT','Managing+and+operating+ICT'],
  'critical-and-creative-thinking': ['Inquiring+–+identifying%2C+exploring+and+organising+information+and+ideas','Generating+ideas%2C+possibilities+and+actions','Reflecting+on+thinking+and+processes','Analysing%2C+synthesising+and+evaluating+reasoning+and+procedures'],
  'personal-and-social-capability': ['Self-awareness','Self-management','Social+awareness','Social+management'],
  'ethical-understanding': ['Understanding+ethical+concepts+and+issues','Reasoning+in+decision+making+and+actions','Exploring+values%2C+rights+and+responsibilities'],
  'intercultural-understanding': ['Recognising+culture+and+developing+respect','Interacting+and+empathising+with+others','Reflecting+on+intercultural+experiences+and+taking+responsibility'],
}

# process data
for capability_name in capability_elements:
  results = {}
  process_urls(capability_name, capability_elements[capability_name])

  with open(capability_name+'_GC_elements.json', 'w') as f:
    f.write(json.dumps(results,indent=2))