import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
from time import sleep
from random import randint
import pickle as pkl

states = np.array(['alabama', 'alaska', 'arizona', 'arkansas', 'california',
    'colorado','connecticut', 'delaware', 'florida', 'georgia', 'hawaii',
    'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana',
    'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota',
    'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'newhampshire',
    'newjersey', 'newmexico', 'newyork', 'northcarolina', 'northdakota', 'ohio',
    'oklahoma', 'oregon', 'pennsylvania', 'rhodeisland', 'southcarolina',
    'southdakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia',
    'washington', 'westvirginia', 'wisconsin', 'wyoming'])

# store listings with odd formatting, to be printed at the end
incomplete = []

#convert scraped listings into dataframe
for_dataframe = []

total_requests = 0

def fill_csv():
    """
    all-encompassing function that includes scraping and cleaning the data
    """
    scrape()

    use_pandas().to_csv('homeless_shelters_directory.csv')

    print('\n  COMPLETE')

    print('\n   go back and look at these:')
    for entry in incomplete:
        print('      ' + ' '.join(entry))
    print(f'\n   completed {total_requests} total requests')


def scrape():
    """
    scrapes the urls and fills for_dataframe
    """
    global states
    while states.size != 0:
        url = f'https://www.homelessshelterdirectory.org/{states[0]}.html'
        li_list = get_html(url).select("#triple a")
        cities = get_links(li_list)         # city urls
        print(f'\n  there are {len(cities)} cities in {states[0]}:')

        shelter_urls = set()            # unique shelters in the state

        while cities.size != 0:
            html = get_html(cities[0])
            city = html.select('.breadcrumb li')[2].get_text()
            listings = html.select('.layout_post_2 h4 a')
            links = get_links(listings)          # shelter listings in the city
            for i in links:
                if i not in shelter_urls:
                    shelter_urls.add(i)
            print(f'    finished looking at {city}')
            cities = np.delete(cities, 0)
        broken = ('https://www.homelessshelterdirectory.org/cgi-bin/id/' +
            'shelter.cgi?shelter=')      # broken entry that appears often
        if broken in shelter_urls:
            shelter_urls.remove(broken)
        print(f'\n  completed shelter urls for {states[0]}, ready to write')
        print(f'  {len(shelter_urls)} to do:')

        for s in shelter_urls:
            html = get_html(s)
            # name of shelter
            name = html.select('.entry_title')
            if name:
                name = html.select('.entry_title')[0].get_text().split(
                    '-')[0].strip()
            else:
                name = 'could not find shelter name'
            if len(name.split('  ')) > 1:
                name = ' '.join(name.split('  '))
            # raw contact info
            has_info = html.select('.col_6_of_12 p')
            if has_info:
                contact = has_info[0].get_text()
                data = '  '.join([name, contact])
                print(f'    obtained {name}: {s}')
                for_dataframe.append(data)
        print(f'\n  finished shelters in {states[0]}')
        states = np.delete(states, 0)
    print('\n  finished scraping, starting to clean\n')


def use_pandas():
    """
    uses pandas to clean data as a dataframe

    :return: cleaned dataframe
    """
    return adjust_data(create_df())


def get_html(url):
    """
    retrieves html content of the page

    :param url: a string which represents the url of the page
    :return: html content as a list
    """
    page = requests.get(url)
    code = bs(page.content, 'html.parser')
    global total_requests
    total_requests += 1        # adjust counter

    return list(code.children)[2]


def get_links(lst):
    """
    retrieves links from href tags

    :param lst: a list that contains the selected html content
    :return: numpy array of url strings
    """
    return np.array(list(map(lambda li: li['href'], lst)))


def create_df():
    """
    constructs dataframe columns from contact info

    :return: pandas dataframe where columns are name, address, city, state,
        zip, web, and other
    """
    df = pd.DataFrame(for_dataframe, columns= ['Info'])

    df['Info'] = df['Info'].apply(lambda x: split_contacts(x))

    # get rid of rows that might be Nones
    df = df[df['Info'].apply(lambda x: x is not None)]

    new_df = pd.DataFrame(df['Info'].to_list(), columns=['Name', 'Address',
        'City', 'State', 'Zip', 'Phone', 'Web', 'Facebook', 'Twitter'])
    
    # store the dataframe temporarily - in case cleaning goes awry
    outfile = open('homeless_shelter_df', 'wb')
    pkl.dump(df, outfile)
    outfile.close()

    print('\n  dataframe created and pickled')

    return new_df


def adjust_data(df):
    """
    cleans dataframe

    :param: dataframe
    :return: cleaned dataframe, ready to write to csv
    """
    # these are all specific mixup cases
    def phone_in_zip():
        """
        switches columns when the zip column has a phone numbers (but honestly
        anything longer than a zipcode)
        """
        edit = df[df["Zip"].apply(lambda x: len(x) > 5)]

        if not edit.empty:
            chunk = edit.copy(deep=True)
            to_change = chunk[['Zip', 'Phone', 'Web']]
            chunk[['Phone', 'Web', 'Facebook']] = to_change
            chunk['Zip'] = chunk['Zip'].apply(lambda x: '')
            df[df["Zip"].apply(lambda x: len(x) > 5)] = chunk

    def zip_in_phone():
        """
        switches columns when the phone column has zip codes (full or truncated)
        """
        edit = df[df["Phone"].apply(lambda x: len(x) <= 5)]

        if not edit.empty:
            chunk = edit.copy(deep=True)
            to_change = chunk[['Phone', 'Web', 'Facebook']]
            chunk[['Zip', 'Phone', 'Web']] = to_change
            chunk["Facebook"] = chunk["Facebook"].apply(lambda x: '')
            df[df["Phone"].apply(lambda x: len(x) <= 5)] = chunk

    def is_website(s):
        """
        evaluates if a string is a website

        :param s: a string
        :return: boolean indicating if string is a website
        """
        return 'http' in s or 'www' in s or '.org' in s or '.com' in s

    def web_in_phone():
        """
        switches columns when the phone column has websites
        """
        edit = df[df["Phone"].apply(lambda x: is_website(x))]

        if not edit.empty:
            chunk = edit.copy(deep=True)
            to_change = chunk[['Phone', 'Web']]
            chunk[['Web', 'Facebook']] = to_change
            chunk['Phone'] = chunk['Phone'].apply(lambda x: '')
            df[df["Phone"].apply(lambda x: is_website(x))] = chunk

    def wrong_values(df):
        """
        catches any other blatantly wrong phone/zip columns that aren't the
        previous cases
        """
        st = df[(df["State"].apply(lambda x: len(x) != 2)) | (df["Zip"].apply(
            lambda x: len(x) != 5))].values.tolist()
        df = df[(df["State"].apply(lambda x: len(x) == 2)) & (df["Zip"].apply(
            lambda x: len(x) == 5))]
        incomplete.extend(st)

    df.drop_duplicates(inplace=True, subset=['Name', 'Address', 'City', 'State',
        'Zip', 'Phone'])
    
    # takes care of individual Nones - allows applying len() 
    df.replace({None : ''}, inplace=True)

    print('\n  dropped duplicate entries and replaced Nones with empty string')

    phone_in_zip()

    zip_in_phone()

    web_in_phone()

    wrong_values(df)
    
    # fb and twitter websites are not useful
    df.drop(['Facebook', 'Twitter'], axis=1, inplace=True)

    print('\n  finished cleaning data')

    return df


def split_contacts(str):
    """
    cleans raw contact info

    :param str: a string containing the contact info for the shelter
    :return: a list of strings where the contact info is separated by
        street address, city, state, zipcode, website, and other
    """
    new = ''
    for i in str:
        if i != '\n' and i != '\r' and i != ':' and i != ',':
            # instead of calling replace 3 times (3n), just rebuild (n)
            new = ''.join([new, i])
    new = [char for char in new.strip().split('  ') if char != '']
   
    try:
        # city, state, and zipcode are often in one string - must separate
        temp = new[2].split()
        # formatting can be very strange, hence the specific cases
        if len(temp) == 1 or (len(temp) == 2 and len(temp[-1]) > 2):
            temp = new[3].split()
            new.insert(4, temp[-1::][0])
            new[3] = temp[-2:-1:][0]
        else:
            if len(temp[-1]) == 2:
                temp.append(' ')
            new.insert(3, temp[-1::][0])
            new.insert(3, temp[-2:-1:][0])
            new[2] = ' '.join(temp[:-2:])
        new = [s.strip() for s in new]
        return new
    except IndexError:
        # sometimes data has weird spacing or symbols, producing IndexError
        print(f"   INDEX ERROR at {' '.join(new)}, appending to incomplete")
        if new is not None:
            incomplete.append(new)


def main():
    fill_csv()


if __name__ == "__main__":
    main()
