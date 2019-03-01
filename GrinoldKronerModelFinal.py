import good_morning as gm
import pandas_datareader.data as web
import bs4 as bs
import urllib.request
import pandas as pd
import numpy as np
import math
import time

# Function to add closing prices to key financials data frame
def addPrices(kr_keyfin, stock, datelist):
    data = web.get_data_yahoo(stock,'01/01/2009', interval='d')['Adj Close']
    yearEndPrices =[]
    for day in datelist:
        yearEndPrices.append(data.loc[day])
    yearEndPrices.append(0) #have to eventually tune to check if recent year's financials are available
    kr_keyfin['Closing Prices'] = yearEndPrices
        
# Function to retrieve analyst consensus for revenue growth
def getConRevG(stock):
    sauce = urllib.request.urlopen('https://finance.yahoo.com/quote/' + stock + '/analysis/')
    soup = bs.BeautifulSoup(sauce,'lxml')
    table = soup.find_all( 'table' , class_='W(100%) M(0) BdB Bdc($c-fuji-grey-c) Mb(25px)')
    df = pd.read_html(str(table))[1].set_index('Revenue Estimate')
    yearlyEstimates = df.iloc[:,-2:]
    currentYrEst = float(df.loc['Sales Growth (year/est)'][-2][:-1])
    nextYrEst = float(df.loc['Sales Growth (year/est)'][-1][:-1])
    avgYrEst = (currentYrEst + nextYrEst) / 2
    return avgYrEst

# Function to estimate growth because on historical average
def getAverageRevG(kr_keyfin, years):
    kr_keyfin['PctRevenueChange'] = kr_keyfin['Revenue USD Mil'].pct_change()
    historicalRevG = kr_keyfin['PctRevenueChange'].rolling(years).mean().iloc[-1]*100
    if np.isnan(historicalRevG):
        historicalRevG = 0
    return historicalRevG
# To add estimation of margin expansions to complete earnings growth component

# Function to return average dividend yield 
def getAverageDivYield(kr_keyfin, years):
    kr_keyfin['Dividend Yield'] =  (kr_keyfin['Dividends USD'] / kr_keyfin['Closing Prices'])
    AverageDivYield = kr_keyfin['Dividend Yield'].rolling(years).mean().iloc[-2]*100
    if np.isnan(AverageDivYield):
        AverageDivYield = 0
    return AverageDivYield

# Function to return Change in Shares Outstanding
def getChangeInSO(kr_keyfin, years):
    kr_keyfin['Change in SO'] = kr_keyfin['Shares Mil'].pct_change()
    changeInSo = kr_keyfin['Change in SO'].rolling(years).mean().iloc[-2]*100
    if np.isnan(changeInSo):
        changeInSo = 0
    return changeInSo

# Function to return annual multiples expansion or contraction
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


# Function to calculate overall expected returns based on the Grinold and Kroner Model
def GrinoldKroner (stock, years, inhorizon, datelist):
    
    print('-------------------- ANALYSIS OF ' + stock + ' --------------------')
    kr = gm.KeyRatiosDownloader()
    kr_frames = kr.download(stock)
    kr_keyfin = kr_frames[0].transpose()
    addPrices(kr_keyfin,stock,datelist)

    # Further refining of decision process for best revenue growth 
    print('- ESTIMATING REVENUE GROWTH -')
    gk_revenueGrowth = getAverageRevG(kr_keyfin, years)
    print( "   " + str(years) + ' historical year average revenue growth is ' + str(gk_revenueGrowth) + '%')
    gk_consensusGrowth = getConRevG(stock)
    print( '   Analyst consensus growth rate of ' + str(gk_consensusGrowth) + '%')
    if gk_consensusGrowth > gk_revenueGrowth:
        gk_conservativeGrowth = gk_revenueGrowth
        print('> Conservative growth rate is set to historical growth rate of ' + str(gk_conservativeGrowth))
    else:
        gk_conservativeGrowth = gk_consensusGrowth
        print('> Conservative growth rate is set to analyst consensus of ' + str(gk_conservativeGrowth))

    gk_divYield = getAverageDivYield(kr_keyfin, years)
    gk_changeInSo = getChangeInSO(kr_keyfin, years)
    gk_annualExCon = getAnnMultiples(stock, inhorizon)

    print('')
    print('- OTHER ESTIMATES -')
    print( str(years) + ' historical year average dividend yield is ' + str (gk_divYield) + '%' )
    print( str(years) + ' historical year average change in shares outstanding ' + str (gk_changeInSo) + '%' )
    print( 'Annual Multiples change over next ' + str(inhorizon) + ' yeaars is ' + str (gk_annualExCon) + '%' )
    print('')
    returns = gk_conservativeGrowth + gk_divYield - gk_changeInSo + gk_annualExCon

    print('Expected returns for ' + stock + ' is ' + str(returns) + '%')
    print('')
    print('')


# Allows for input of multiple stock tickers
def GrinoldKronerList(stocklist, years, inhorizon, datelist):
    for stock in stocklist:
        GrinoldKroner(stock, years, inhorizon, datelist)
        time.sleep(5)


# Sample Inputs
closingpricedates = ['2010-12-31','2010-12-31','2011-12-30','2012-12-31','2013-12-31','2014-12-31','2015-12-31','2016-12-30','2017-12-29','2018-12-31']
stockListTest = ['AAPL','NVDA','AMAT']
stockListElec = ['AVGO','INTC','MRVL','MU','NVDA']

GrinoldKronerList(stockListElec,3,7,closingpricedates)