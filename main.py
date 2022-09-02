from bs4 import BeautifulSoup
import json
import requests


def table_data_text(table):
    """Parses a html segment started with tag <table> followed
    by multiple <tr> (table rows) and inner <td> (table data) tags.
    It returns a list of rows with inner columns.
    Accepts only one <th> (table header/data) in the first row.
    https://stackoverflow.com/questions/2935658/beautifulsoup-get-the-contents-of-a-specific-table
    """

    def rowget_data_text(tr, coltag='td'):  # td (data) or th (header)
        return [td.get_text(strip=True) for td in tr.find_all(coltag)]

    rows = []
    trs = table.find_all('tr')
    headerow = rowget_data_text(trs[0], 'th')
    if headerow:  # if there is a header row include first
        rows.append(headerow)
        trs = trs[1:]
    for tr in trs:  # for every table row
        rows.append(rowget_data_text(tr, 'td'))  # data row
    return rows


url = 'https://storage.googleapis.com/infosimples-public/commercia/case/product.html'
final_answer = {}

response = requests.get(url)
parsed_html = BeautifulSoup(response.text, 'html.parser')

# TITLE
final_answer['title'] = parsed_html.select_one('h2#product_title').get_text()

# BRAND
final_answer['brand'] = parsed_html.select_one('div.brand').get_text()

# CATEGORIES
final_answer['categories'] = parsed_html.select_one('nav.current-category').get_text().replace('\n', '').split('>')
categories = list()
for category in final_answer['categories']:
    category = category.strip()
    categories.append(category)
final_answer['categories'] = categories

# DESCRIPTION
final_answer['description'] = parsed_html.select_one('div.product-details').get_text()
description = final_answer['description'].replace('Description', '').strip('\n')
description_list = description.split('\n')
rows = []
for row in description_list:
    row = row.strip()
    rows.append(row)
final_answer['description'] = ' '.join(rows).strip()

# SKUS - arrumar
skus_html = parsed_html.find('div', {'class': 'skus-area'})
sku_cards_html = skus_html.findAll('div', {'class': 'card'})
final_answer['skus'] = list()
for sku_card in sku_cards_html:
    sku = {
        'name': None,
        'old_price': None,
        'current_price': None,
        'available': None
    }

    sku_name = sku_card.find('div', {'class': 'sku-name'})
    if sku_name is not None:
        sku['name'] = sku_name.get_text().strip().strip('\n')

    sku_current_price = sku_card.find('div', {'class': 'sku-current-price'})
    if sku_current_price is not None:
        sku['current_price'] = float(sku_current_price.get_text().replace('$', '').strip().strip('\n'))

    sku_old_price = sku_card.find('div', {'class': 'sku-old-price'})
    if sku_old_price is not None:
        sku['old_price'] = float(sku_old_price.get_text().replace('$', '').strip().strip('\n'))

    # IF THE PRICE IS NULL, SO WE CAN ASSUME THE SKU IS OUT OF STOCK.
    if sku_current_price is not None:
        sku['available'] = True
    else:
        sku['available'] = False

    final_answer['skus'].append(sku)

# PRODUCT PROPERTIES
tables = parsed_html.findAll('table')
product_properties = tables[0]

additional_properties = tables[1]
product_properties_data = table_data_text(product_properties)
final_answer['properties'] = []
for product_property in product_properties_data:
    property = {'label': product_property[0], 'value': product_property[1]}
    final_answer['properties'].append(property)

# ADDITIONAL PROPERTIES
additional_properties = tables[1]
additional_properties_data = table_data_text(additional_properties)
# skip header
for additional_property in additional_properties_data[1:]:
    property = {'label': additional_property[0], 'value': additional_property[1]}
    final_answer['properties'].append(property)

# REVIEWS - AVERAGE SCORE
reviews_html = parsed_html.find('div', {"id": "comments"})
review_average_score_text = reviews_html.find('h4').get_text()
# here we split the "Average score: 3.3/5" to get the numerical part and parse to float
review_average_score_parsed = float(review_average_score_text.split()[2].split('/')[0])
final_answer['review_average_score'] = review_average_score_parsed

# REVIEWS - COMMENTS
reviews_comments_html = parsed_html.findAll('div', {"class": "review-box"})

reviews = []
for review_comment_html in reviews_comments_html:
    # print(review_comment_html)
    name = review_comment_html.find('span', {"class": "review-username"}).get_text()
    data = review_comment_html.find('span', {"class": "review-date"}).get_text()
    score = review_comment_html.find('span', {"class": "review-stars"}).get_text()
    text = review_comment_html.find('p').get_text()
    review = dict()

    review['name'] = name
    review['data'] = data
    review['score'] = score.replace('\u00e2\u0098\u0085', '*').count('*')
    review['text'] = text
    reviews.append(review)

final_answer['reviews'] = reviews

# URL
final_answer['url'] = url

# how to sort json
# https://stackoverflow.com/questions/12943819/how-to-prettyprint-a-json-file
# how to solve special characters in json
# https://stackoverflow.com/questions/18337407/saving-utf-8-texts-with-json-dumps-as-utf-8-not-as-a-u-escape-sequence
json_resposta_final = json.dumps(final_answer, indent=2, ensure_ascii=False)
with open('produto.json', mode='w', encoding='latin1') as json_file:
    json_file.write(json_resposta_final)
