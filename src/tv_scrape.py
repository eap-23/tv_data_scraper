import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import os
from os import mkdir
from os.path import isdir
from time import sleep
from random import randint
from time import time
from bs4 import BeautifulSoup
import requests

def remove_str(votes):
    for r in ((',',''), ('(', ''), (')', '')):
        votes = votes.replace(*r)

    return votes

def get_df(url):
    print("\nPlease wait while program scapes data from IMDB!")
    
    main_response = requests.get(url)

    main_html = BeautifulSoup(main_response.text, 'lxml')

    show_title = main_html.find('div', class_="title_wrapper").h1.text
    show_title = show_title.rstrip()

    numSeasons = main_html.find('div', class_='seasons-and-year-nav').a.text
    numSeasons = int(numSeasons)

    request_url = url + 'episodes?season='
 
    num_request = 0
    start_time = time()

    episodes = []
    
    try:
        for sn in range(1, numSeasons + 1):

            #Pause the loop
            sleep(randint(8,10))
            
            #Make get request for season page
            response = requests.get(request_url + str(sn))

            #Pause the loop
            # sleep(randint(8,10))

            #Monitor the request
            num_request += 1
            elapsed_time = time() - start_time
            print ('Request: ' + 'Season ' + str(num_request) + '; Frequency: ' + str(num_request/elapsed_time) + ' requests/s')

            #Parse content with Beautiful Soup
            page_html = BeautifulSoup(response.text, 'lxml')

            episode_containers = page_html.find_all('div', class_='info')

            for episode in episode_containers:
                season = sn
                title = episode.a['title']
                    
                #Below code block based on following assumptions:
                #1. An episode with no data will be titled in 'Episode #1.1' syntax
                #2. There will be no episodes with data after the first instance
                #Both for loops will break if episode with no data encountered and df will be generated
                if title.startswith('Episode #' + str(sn) + '.'):
                    raise StopIteration
                
                else:
                    episodeNum = episode.meta['content']
                    airdate = episode.find('div', class_='airdate').text.strip()
                    rating = episode.find('span', class_="ipl-rating-star__rating").text
                    totalVotes = episode.find('span', class_="ipl-rating-star__total-votes").text
                    epDescription = episode.find('div', class_='item_description').text.strip()

                    episode_data = [show_title, season, episodeNum, title, airdate, rating, totalVotes, epDescription]

                    episodes.append(episode_data)
    except StopIteration:
        pass

    df = pd.DataFrame(episodes, columns = ['show_title', 'season', 'episode_number', 'title', 
                                'airdate', 'rating', 'total_votes', 'desc'])
    
    df['total_votes'] = df.total_votes.apply(remove_str).astype(int)

    df['rating'] = df.rating.astype(float)

    df['airdate'] = pd.to_datetime(df.airdate)
    
    df['episode_number'] = df.episode_number.astype(int)

    # df.insert(0, 'show_title', show_title)

    return df, show_title

#===============Create CSV File and Folders========================================
def generate_csv(df, show_title):
    showFolder = show_title.replace(" ", "_").lower()
    parentFolderPath = os.path.join(os.path.expanduser("~"), 'Documents', 'tv_show_data')
    folderPath = os.path.join(os.path.expanduser("~"), 'Documents', 'tv_show_data', showFolder)
    fullPath = os.path.join(os.path.expanduser("~"), 'Documents', 
                            'tv_show_data', showFolder,
                            'data.csv')

    if not isdir(parentFolderPath):
        mkdir(parentFolderPath)
    else:
        pass
        
    if not isdir(folderPath):
        mkdir(folderPath)
    else:
        pass

    df.to_csv(fullPath, index=False)
    
    return folderPath

#===============Line Plot=================================================
def generate_plots(df, folderPath, show_title):
    
    #Make copies of original df to be used for boxplot and heatmap below
    box_df = df.copy()
    heat_df = df.copy()

    df['x'] = np.where(df['episode_number'].isin(range(1,10)), df['season'].astype(str) + 
		'x0' + df['episode_number'].astype(str),
		df['season'].astype(str) + 'x' + df['episode_number'].astype(str))

    plt.style.use('ggplot')

    seasons = df['season'].drop_duplicates().to_list()

    fig1 = plt.figure(1, figsize=(12, 6), dpi=200)

    #Initialize the below to be used in for loop in next code block
    #n will track where next tick_mark/label should go
    #tick_mark and label placed at middle of each season line
    n = 0
    tick_label = 0
    tick_marks = []
    tick_labels = []
    
    for season in seasons:
        index = df[df['season'] != season].index
        df2 = df.drop(index)
        
        x = df2['x'].to_list()
        # x = df2['airdate'].to_list()
        y = df2['rating'].to_list()

        plt.plot(x, y, marker=".")
        
        tick_mark = len(x)/2 + n
        n = len(x) + n
        
        tick_label = tick_label + 1
        
        tick_marks.append(tick_mark)
        tick_labels.append(tick_label)

    plt.xticks(ticks=tick_marks, labels=tick_labels)

    plt.ylabel('IMDB Rating')
    plt.xlabel('Season')
    plt.title(show_title, fontweight='bold', pad=10)
    
    #========Box Plot============================ 
    fig2 = plt.figure(2, figsize=(6, 6), dpi=200)

    seasons = box_df['season'].to_list()
    ratings = box_df['rating'].to_list()

    ax = sns.boxplot(x=seasons, y=ratings, palette="Set1")

    ax.set_xlabel('Season')
    ax.set_ylabel('IMDB Rating')

    ax.set_title(show_title, fontweight='bold', pad=10)

#=======Heat Map=============================
    fig3 = plt.figure(3, figsize=(6, 6), dpi=200)

    heat_df = heat_df.pivot(index='episode_number', columns='season', values='rating')

    myColors = (('#4c566a'), ('#bf616a'), ('#d08770'), ('#ebcb8b'), ('#a3be8c'))
    cmap = LinearSegmentedColormap.from_list('Custom', myColors, len(myColors))

    with sns.axes_style("whitegrid"):	
        ax2 = sns.heatmap(heat_df, annot=True, cmap=cmap, vmin=5, vmax=10,linewidths=0.1, linecolor='white', rasterized=False, mask=heat_df.isnull())

    colorbar = ax2.collections[0].colorbar
    colorbar.set_ticks([5.5, 6.5, 7.5, 8.5, 9.5])
    colorbar.set_ticklabels(['Bad', 'Meh', 'Average', 'Good', 'Great'])

    ax2.set_xlabel('Season')
    ax2.xaxis.set_label_position('top')
    ax2.xaxis.tick_top()

    ax2.set_ylabel('Episode')
    ax2.tick_params(axis = 'y', labelrotation = 0, left=False)
    ax2.tick_params(axis = 'x', top=False)
    
    ax2.set_title(show_title, loc='left', fontweight='bold', pad=10)

    plt.tight_layout()
    # plt.show()
    
    fig1.savefig(folderPath + "/fig1.png")
    fig2.savefig(folderPath + "/fig2.png")
    fig3.savefig(folderPath + "/fig3.png")
    
    print('\nSuccess! Data and figures saved here: ' + folderPath)

def main():
    show_url = input("\nEnter IMDB url for TV Show: ")
    df, show_title = get_df(show_url)
    folderPath = generate_csv(df, show_title)
    generate_plots(df, folderPath, show_title)
    
if __name__ == "__main__":
    main()  

