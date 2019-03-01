import good_morning as gm
import pandas_datareader.data as web
import bs4 as bs
import urllib.request
import pandas as pd
import numpy as np
import math
import time
pd.set_option('display.expand_frame_repr', False)


closingpricedates = ['2010-12-31','2010-12-31','2011-12-30','2012-12-31','2013-12-31','2014-12-31','2015-12-31','2016-12-30','2017-12-29','2018-12-31']

def getAverageRevG(kr_keyfin, years):
    kr_keyfin['PctRevenueChange'] = kr_keyfin['Revenue USD Mil'].pct_change()
    averageRevG = kr_keyfin['PctRevenueChange'].rolling(years).mean().iloc[-1]*100
    if np.isnan(averageRevG):
        averageRevG = 0
    return averageRevG


def addPrices(kr_keyfin, stock, datelist):
    data = web.get_data_yahoo(stock,'01/01/2009', interval='d')['Adj Close']
    yearEndPrices =[]
    for day in datelist:
        yearEndPrices.append(data.loc[day])
    yearEndPrices.append(0) #have to eventually tune to check if recent year's financials are available
    kr_keyfin['Closing Prices'] = yearEndPrices
        

def getAverageDivYield(kr_keyfin, years):
    kr_keyfin['Dividend Yield'] =  (kr_keyfin['Dividends USD'] / kr_keyfin['Closing Prices'])
    AverageDivYield = kr_keyfin['Dividend Yield'].rolling(years).mean().iloc[-2]*100
    if np.isnan(AverageDivYield):
        AverageDivYield = 0
    return AverageDivYield

def getChangeInSO(kr_keyfin, years):
    kr_keyfin['Change in SO'] = kr_keyfin['Shares Mil'].pct_change()
    changeInSo = kr_keyfin['Change in SO'].rolling(years).mean().iloc[-2]*100
    if np.isnan(changeInSo):
        changeInSo = 0
    return changeInSo


def getAnnMultiples(stock, inhorizon):
    sauce = urllib.request.urlopen('https://www.macrotrends.net/stocks/charts/' + stock + '/nvidia/pe-ratio').read()
    soup = bs.BeautifulSoup(sauce,'lxml')
    
    table  = soup.find_all('table',class_='table')[0]
    df = pd.read_html(str(table))[0]
    latestPE = df['Unnamed: 3'].iloc[1]
    medianPE = df['Unnamed: 3'].median()
    multiplesExCon  = (medianPE / latestPE - 1)*100
    annualExCon = multiplesExCon / inhorizon
    if np.isnan(annualExCon):
        annualExCon = 0
    return annualExCon


def GrinoldKroner (stock, years, inhorizon, datelist):
    
    kr = gm.KeyRatiosDownloader()
    kr_frames = kr.download(stock)
    kr_keyfin = kr_frames[0].transpose()

    addPrices(kr_keyfin,stock,datelist)
    gk_revenueGrowth = getAverageRevG(kr_keyfin, years)
    gk_divYield = getAverageDivYield(kr_keyfin, years)
    gk_changeInSo = getChangeInSO(kr_keyfin, years)
    gk_annualExCon = getAnnMultiples(stock, inhorizon)

    print('-------------------- ANALYSIS OF ' + stock + ' --------------------')
    print( str(years) + ' historical year average revenue growth is ' + str(gk_revenueGrowth) + '%')
    print( str(years) + ' historical year average dividend yield is ' + str (gk_divYield) + '%' )
    print( str(years) + ' historical year average change in shares outstanding ' + str (gk_changeInSo) + '%' )
    print( 'Annual Multiples change over next ' + str(inhorizon) + ' yeaars is ' + str (gk_annualExCon) + '%' )
    print('')
    returns = gk_revenueGrowth + gk_divYield - gk_changeInSo + gk_annualExCon

    print('Expected returns for ' + stock + ' is ' + str(returns) + '%')
    print('')
    print('')


def GrinoldKronerList(stocklist, years, inhorizon, datelist):
    for stock in stocklist:
        GrinoldKroner(stock, years, inhorizon, datelist)
        time.sleep(5)


stockListTest = ['AAPL','NVDA','AMAT']
stockListSemi = ['AVGO','INTC','MRVL','MU','NVDA']

GrinoldKronerList(stockListSemi,3,7,closingpricedates)