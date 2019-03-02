import pandas_datareader.data as web
import bs4 as bs
import urllib.request
import pandas as pd
import numpy as np
import math
import time
import good_morning as gm

# Function to add closing prices to key financials data frame
def addPrices(kr_keyfin, stock, datelist):
    data = web.get_data_yahoo(stock,'01/01/2009', interval='d')['Adj Close']
    yearEndPrices =[]
    for day in datelist:
        yearEndPrices.append(data.loc[day])
    yearEndPrices.append(0) #have to eventually tune to check if recent year's financials are available
    kr_keyfin['Closing Prices'] = yearEndPrices
        
# Function to include analyst consensus for revenue growth
# To further refine in future by using long term growth
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

def displayKeyFinancials(kr_frames):
    #Calculating Revenue Growth
    keyfinancials = kr_frames[0].drop(kr_frames[0].index[1:])
    revenueGrowth = kr_frames[0].iloc[0].pct_change()*100
    revenueGrowth.name = 'Revenue Growth'
    keyfinancials = keyfinancials.append(revenueGrowth)
    #Profitability Measures
    keyfinancials = keyfinancials.append(kr_frames[2].loc['Return on Invested Capital %']) #ROIC
    keyfinancials = keyfinancials.append(kr_frames[0].iloc[[3,12]]) #Operating Margin and FCF
    #Ability to maintain dividend payout
    totalDividends = kr_frames[0].iloc[6] *  kr_frames[0].iloc[8]
    totalDividends.name = 'Total Dividends'
    keyfinancials = keyfinancials.append(totalDividends)
    #Degree of leverage
    keyfinancials = keyfinancials.append(kr_frames[9].iloc[[2]]) #Operating Margin and FCF
    #Cleaning up table for display
    keyfinancials.drop( keyfinancials.columns[len(keyfinancials.columns)-1],axis = 1, inplace=True) #drops inaccurate forecasted data 
    keyfinancials = np.round(keyfinancials,decimals=2) #rounds to 2 decimals
    print(keyfinancials)


# Function to calculate overall expected returns based on the Grinold and Kroner Model
def GrinoldKroner (stock, years, inhorizon, datelist,roundDec):
    
    print('------------------------- ANALYSIS OF ' + stock + ' -------------------------')
    # Initial download of data key financials
    kr = gm.KeyRatiosDownloader()
    kr_frames = kr.download(stock)
    kr_keyfin = kr_frames[0].transpose()
    addPrices(kr_keyfin,stock,datelist)

    # Estimating revenue growth (to further refine decision process)
    print('\n- ESTIMATING REVENUE GROWTH -')
    gk_revenueGrowth = getAverageRevG(kr_keyfin, years)
    print(str(years) + ' historical year average revenue growth is ' + str(round(gk_revenueGrowth,roundDec
)) + '%')
    gk_consensusGrowth = round(getConRevG(stock),roundDec
)
    print('Analyst consensus growth rate of ' + str(gk_consensusGrowth) + '%')
    if gk_consensusGrowth > gk_revenueGrowth:
        gk_conservativeGrowth = gk_revenueGrowth
        print('> Conservative growth rate is set to historical growth rate of ' + str(gk_conservativeGrowth) + '%')
    else:
        gk_conservativeGrowth = gk_consensusGrowth
        print('> Conservative growth rate is set to analyst consensus of ' + str(gk_conservativeGrowth) + '%')

    # Calculation of other components
    gk_divYield = getAverageDivYield(kr_keyfin, years)
    gk_changeInSo = getChangeInSO(kr_keyfin, years)
    gk_annualExCon = getAnnMultiples(stock, inhorizon)

    # Displaying overall findings
    print('\n- ESTIMATING DIVIDEND YIELD, CHANGE IN SO AND MULTIPLES EXPANSION -')
    print( '> historical average dividend yield is ' + str (round(gk_divYield,roundDec
)) + '%' )
    print( '> historical average change in shares outstanding ' + str (round(gk_changeInSo,roundDec
)) + '%' )
    print( '> Annual Multiples change over next ' + str(inhorizon) + ' yeaars is ' + str (round(gk_annualExCon,roundDec
)) + '%' )
    print('')
    expectedreturns = gk_conservativeGrowth + gk_divYield - gk_changeInSo + gk_annualExCon
    print('>>> Final expected returns based on the Grinold & Kroner Model for ' + stock + ' is ' + str(round(expectedreturns,roundDec
)) + '% \n')

    # Displays selected important financials
    print('\n- SELECTED KEY FINANCIALS -')
    displayKeyFinancials(kr_frames)
    print('\n' *2)


# Allows for input of multiple stock tickers
def GrinoldKronerList(stocklist, years, inhorizon, datelist, roundDec):
    for stock in stocklist:
        GrinoldKroner(stock, years, inhorizon, datelist, roundDec)
        time.sleep(10)


# # Sample Parameters and Input
# histAvgYears = 3
# investHorizon = 7
# roundedDecimal = 4
# closingpricedates = ['2010-12-31','2010-12-31','2011-12-30','2012-12-31','2013-12-31','2014-12-31','2015-12-31','2016-12-30','2017-12-29','2018-12-31']
# stockListShort = ['AAPL','NVDA','AMAT']
# stockListElec = ['MU','NVDA','TXN','QCOM','AVGO','INTC','MRVL']
# pd.set_option('display.expand_frame_repr', False)


# GrinoldKronerList(stockListElec,histAvgYears,investHorizon,closingpricedates,roundedDecimal)