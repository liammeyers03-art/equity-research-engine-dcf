import yfinance as yf
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize

API_KEY = 'STm6gxQHw0d3C2SLjqlvvaBQ99PJ2WV8'
BASE_PATH = r"C:\Users\liamm\OneDrive\Analytics\Python Projects\QuantTerminal\Equity Research Engine"


def get_stock_universe():
    path = BASE_PATH + r'\screener_universe.xlsx'
    screener_df = pd.read_excel(path)
    screener_df.columns = ['Ticker']
    screener_df['Ticker'] = screener_df['Ticker'].astype(str).str.strip().str.upper()
    stock_universe = screener_df['Ticker'].tolist()
    return stock_universe

# =========================
# GET RATIOS & METRICS 
# =========================  

def load_existing_data():
    path = BASE_PATH + r'\fundamental_data.xlsx'
    file_path = BASE_PATH + r'\unavailable_tickers.xlsx'
    existing_ratios_df = pd.read_excel(path, sheet_name='Ratios')
    existing_metrics_df = pd.read_excel(path, sheet_name='Metrics')
    existing_unavaialble_tickers_df = pd.read_excel(file_path)
    existing_unavaialble_tickers = existing_unavaialble_tickers_df['Ticker'].tolist()
    existing_tickers = set(existing_ratios_df['symbol'])

    return existing_ratios_df, existing_metrics_df, existing_tickers, existing_unavaialble_tickers_df, existing_unavaialble_tickers

def get_target_tickers(stock_universe,existing_tickers,existing_unavaialble_tickers):
    existing_unavaialble_tickers = set(existing_unavaialble_tickers)
    new_tickers = set(stock_universe)
    target_tickers = new_tickers - existing_tickers - existing_unavaialble_tickers
    target_tickers = list(target_tickers)
    
    return target_tickers

def load_new_ratios(existing_ratios_df,existing_metrics_df,target_tickers,existing_unavaialble_tickers_df):
    new_ratios_df, unavailable_tickers = get_ttm_financial_ratios(target_tickers,API_KEY)
    unavailable_tickers_df = pd.DataFrame(unavailable_tickers)

    new_metrics_df = get_ttm_key_metrics(target_tickers,API_KEY)

    updated_ratios_df = pd.concat([existing_ratios_df,new_ratios_df],ignore_index=True)
    updated_metrics_df = pd.concat([existing_metrics_df,new_metrics_df],ignore_index=True)
    updated_unavailable_tickers_df = pd.concat([existing_unavaialble_tickers_df,unavailable_tickers_df],ignore_index=True)

    updated_ratios_df = updated_ratios_df.drop_duplicates(subset='symbol',keep='last')
    updated_metrics_df = updated_metrics_df.drop_duplicates(subset='symbol',keep='last')

    return updated_ratios_df, updated_metrics_df, updated_unavailable_tickers_df

def get_ttm_financial_ratios(target_tickers,API_KEY):

    ratios_data = []
    unavailable_tickers = []
    
    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/ratios-ttm?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)
        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            dct = {'Ticker':i,'DataSet':'Ratios','Status':response.status_code}
            unavailable_tickers.append(dct)
            continue

        data = response.json()

        if isinstance(data,list) & (len(data) > 0):
            ratios_data.extend(data)
            
    ratios_df = pd.DataFrame(ratios_data)

    return ratios_df, unavailable_tickers


def get_ttm_key_metrics(target_tickers,API_KEY):
    metrics_data = []
    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/key-metrics-ttm?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)
        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue

        data = response.json()

        if isinstance(data,list) & (len(data) > 0):
            metrics_data.extend(data)
        
    metrics_df = pd.DataFrame(metrics_data)
    return metrics_df
 
# =========================
# CREATE STOCK SCREENER
# =========================

def create_scoring_metrics(ratios_df,metrics_df):
    df = pd.DataFrame()
    df['Symbol'] = ratios_df['symbol']

    #Growth 
    foward_price_to_earnings_growth_conditions = [
        (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] > 0) & (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] < 1.0),
        (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] > 0) & (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] < 1.5),
        (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] > 0) & (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] < 2.5),
        (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] > 0) & (ratios_df['forwardPriceToEarningsGrowthRatioTTM'] < 4.0)
    ]
    foward_price_to_earnings_points = [20,12,8,5]
    df['FowardPriceToEarningsGrowth'] = ratios_df['forwardPriceToEarningsGrowthRatioTTM']
    df['FowardPriceToEarningsGrowthPoints'] = np.select(foward_price_to_earnings_growth_conditions,foward_price_to_earnings_points,default=0 )

    #Valuation
    price_to_earnings_conditions = [
        (ratios_df['priceToEarningsRatioTTM'] >0) & (ratios_df['priceToEarningsRatioTTM'] < 15),
        (ratios_df['priceToEarningsRatioTTM'] >0) & (ratios_df['priceToEarningsRatioTTM'] < 22),
        (ratios_df['priceToEarningsRatioTTM'] >0) & (ratios_df['priceToEarningsRatioTTM'] < 30),
        (ratios_df['priceToEarningsRatioTTM'] >0) & (ratios_df['priceToEarningsRatioTTM'] < 40)
    ]
    price_to_earnings_points = [10,8,5,2]
    df['PriceToEarnings'] = ratios_df['priceToEarningsRatioTTM']
    df['PriceToEarningsPoints'] = np.select(price_to_earnings_conditions,price_to_earnings_points,default=0)
    
    price_to_free_cash_flow_conditions = [
        (ratios_df['priceToFreeCashFlowRatioTTM'] >0) & (ratios_df['priceToFreeCashFlowRatioTTM'] < 15),
        (ratios_df['priceToFreeCashFlowRatioTTM'] >0) & (ratios_df['priceToFreeCashFlowRatioTTM'] < 25),
        (ratios_df['priceToFreeCashFlowRatioTTM'] >0) & (ratios_df['priceToFreeCashFlowRatioTTM'] < 35),
        (ratios_df['priceToFreeCashFlowRatioTTM'] >0) & (ratios_df['priceToFreeCashFlowRatioTTM'] < 50)
    ]
    price_to_free_cash_flow_points = [10,8,5,2]
    df['PriceToFCF'] = ratios_df['priceToFreeCashFlowRatioTTM']
    df['PriceToFreeCashFlowPoints'] = np.select(price_to_free_cash_flow_conditions,price_to_free_cash_flow_points,default=0)

    enterprise_to_ebitda_conditions = [
        (metrics_df['evToEBITDATTM'] >0) & (metrics_df['evToEBITDATTM'] < 10),
        (metrics_df['evToEBITDATTM'] >0) & (metrics_df['evToEBITDATTM'] < 16),
        (metrics_df['evToEBITDATTM'] >0) & (metrics_df['evToEBITDATTM'] < 24),
        (metrics_df['evToEBITDATTM'] >0) & (metrics_df['evToEBITDATTM'] < 35)
    ]
    enterprise_to_ebitda_points = [10,8,5,2]
    df['EnterpriseValueToEBITDA'] = metrics_df['evToEBITDATTM']
    df['EnterpriseToEbitdaPoints'] = np.select(enterprise_to_ebitda_conditions,enterprise_to_ebitda_points,default=0)

    fcf_yield_conditions = [
        (metrics_df['freeCashFlowYieldTTM'] > .08),
        (metrics_df['freeCashFlowYieldTTM'] > .05),
        (metrics_df['freeCashFlowYieldTTM'] > .03),
        (metrics_df['freeCashFlowYieldTTM'] > .01)
    ]
    fcf_yield_points = [10,8,5,2]
    df['FCFYield'] = metrics_df['freeCashFlowYieldTTM']
    df['FCFYieldPoints'] = np.select(fcf_yield_conditions, fcf_yield_points, default=0)

    # Profitability

    roe_conditions = [
        (metrics_df['returnOnEquityTTM'] > .25),
        (metrics_df['returnOnEquityTTM'] > .18),
        (metrics_df['returnOnEquityTTM'] > .12),
        (metrics_df['returnOnEquityTTM'] > .08)
    ]
    roe_points = [10,8,5,2]
    df['ROE'] = metrics_df['returnOnEquityTTM']
    df['ROEPoints'] = np.select(roe_conditions, roe_points, default=0)

    roic_conditions = [
        (metrics_df['returnOnInvestedCapitalTTM'] > .20),
        (metrics_df['returnOnInvestedCapitalTTM'] > .15),
        (metrics_df['returnOnInvestedCapitalTTM'] > .10),
        (metrics_df['returnOnInvestedCapitalTTM'] > .05)
    ]
    roic_points = [10,8,5,2]
    df['ROIC'] = metrics_df['returnOnInvestedCapitalTTM']
    df['ROICPoints'] = np.select(roic_conditions, roic_points, default=0)

    gross_profit_margin_conditions = [
        (ratios_df['grossProfitMarginTTM'] > .70),
        (ratios_df['grossProfitMarginTTM'] > .55),
        (ratios_df['grossProfitMarginTTM'] > .40),
        (ratios_df['grossProfitMarginTTM'] > .25)
    ]
    gross_profit_margin_points = [10,8,5,2]
    df['GrossMargin'] = ratios_df['grossProfitMarginTTM']
    df['GrossMarginPoints'] = np.select(gross_profit_margin_conditions, gross_profit_margin_points, default=0)

    operating_profit_margin_conditions = [
        (ratios_df['operatingProfitMarginTTM'] > .30),
        (ratios_df['operatingProfitMarginTTM'] > .22),
        (ratios_df['operatingProfitMarginTTM'] > .15),
        (ratios_df['operatingProfitMarginTTM'] > .08)
    ]
    operating_profit_margin_points = [10,8,5,2]
    df['OperatingMargin'] = ratios_df['operatingProfitMarginTTM']
    df['OperatingMarginPoints'] = np.select(operating_profit_margin_conditions, operating_profit_margin_points, default=0)

    net_profit_margin_conditions = [
        (ratios_df['netProfitMarginTTM'] > .25),
        (ratios_df['netProfitMarginTTM'] > .18),
        (ratios_df['netProfitMarginTTM'] > .10),
        (ratios_df['netProfitMarginTTM'] > .05)
    ]
    net_profit_margin_points = [10,8,5,2]
    df['NetProfitMargin'] = ratios_df['netProfitMarginTTM']
    df['NetMarginPoints'] = np.select(net_profit_margin_conditions, net_profit_margin_points, default=0)

    #Finanical Health 

    debt_to_equity_conditions = [
        (ratios_df['debtToEquityRatioTTM'] >0) & (ratios_df['debtToEquityRatioTTM'] < .30),
        (ratios_df['debtToEquityRatioTTM'] >0) & (ratios_df['debtToEquityRatioTTM'] < .60),
        (ratios_df['debtToEquityRatioTTM'] >0) & (ratios_df['debtToEquityRatioTTM'] < 1.00),
        (ratios_df['debtToEquityRatioTTM'] >0) & (ratios_df['debtToEquityRatioTTM'] < 2.00)
    ]
    debt_to_equity_points = [10,8,5,2]
    df['DebtToEquity'] = ratios_df['debtToEquityRatioTTM']
    df['DebtToEquityPoints'] = np.select(debt_to_equity_conditions, debt_to_equity_points, default=0)

    current_ratio_conditions = [
        (metrics_df['currentRatioTTM'] > 2.0),
        (metrics_df['currentRatioTTM'] > 1.5),
        (metrics_df['currentRatioTTM'] > 1.0),
        (metrics_df['currentRatioTTM'] > 0.75)
    ]
    current_ratio_points = [10,8,5,2]
    df['CurrentRatio'] = metrics_df['currentRatioTTM']
    df['CurrentRatioPoints'] = np.select(current_ratio_conditions, current_ratio_points, default=0)

    net_debt_to_ebitda_conditions = [
        (metrics_df['netDebtToEBITDATTM'] >0) & (metrics_df['netDebtToEBITDATTM'] < 0.5),
        (metrics_df['netDebtToEBITDATTM'] >0) & (metrics_df['netDebtToEBITDATTM'] < 1.5),
        (metrics_df['netDebtToEBITDATTM'] >0) & (metrics_df['netDebtToEBITDATTM'] < 3.0),
        (metrics_df['netDebtToEBITDATTM'] >0) & (metrics_df['netDebtToEBITDATTM'] < 5.0)
    ]
    net_debt_to_ebitda_points = [10,8,5,2]
    df['NetDebtToEbitda'] = metrics_df['netDebtToEBITDATTM']
    df['NetDebtToEbitdaPoints'] = np.select(net_debt_to_ebitda_conditions, net_debt_to_ebitda_points, default=0)


    df['TotalPoints'] = df['FowardPriceToEarningsGrowthPoints'] + df['PriceToEarningsPoints'] + df['PriceToFreeCashFlowPoints'] + df['EnterpriseToEbitdaPoints'] + df['FCFYieldPoints'] + df['ROEPoints'] + df['ROICPoints'] + df['GrossMarginPoints'] + \
    df['OperatingMarginPoints'] + df['NetMarginPoints'] + df['DebtToEquityPoints'] + df['CurrentRatioPoints'] + df['NetDebtToEbitdaPoints']
    df['ScorePct'] = df['TotalPoints'] / 140
    df = df.sort_values(by='ScorePct', ascending=False)
    return df

def rank_stocks(df):
    ranked_df = df.nlargest(100,'ScorePct')
    ranked_df.index = range(1,len(ranked_df)+1)
    return ranked_df

# =========================
# GET COMPANY FINANCIALS & MARKET DATA
# =========================

def pull_existing_data():
    path = BASE_PATH + r'\fundamental_data.xlsx'
    existing_income_statement = pd.read_excel(path,'Income Statement')
    existing_balance_sheet = pd.read_excel(path,'Balance Sheet')
    existing_cash_flow = pd.read_excel(path, 'Cash Flow Statement')
    existing_financial_estimates = pd.read_excel(path, 'Financial Estimates')
    existing_comparable_companies = pd.read_excel(path, 'Comparable Companies')

    return existing_income_statement, existing_balance_sheet, existing_cash_flow, existing_financial_estimates, existing_comparable_companies


def load_new_financials(existing_income_statement, existing_balance_sheet, existing_cash_flow, existing_financial_estimates, existing_comparable_companies, target_stocks, API_KEY):

    new_income_stmt_df = pull_income_statment(target_stocks,API_KEY)
    new_balance_sheet_df = pull_balance_sheet(target_stocks,API_KEY)
    new_cash_flow_df = pull_cashflow_statment(target_stocks,API_KEY)
    new_financial_estimate_df = pull_finanical_estimates(target_stocks,API_KEY)
    new_comparables_df = get_comparable_companies(target_stocks,API_KEY)

    updated_income_statement = pd.concat([existing_income_statement,new_income_stmt_df],ignore_index=True)
    updated_balace_sheet = pd.concat([existing_balance_sheet,new_balance_sheet_df],ignore_index=True)
    updated_cash_flow = pd.concat([existing_cash_flow,new_cash_flow_df],ignore_index=True)
    updated_finanical_estimates = pd.concat([existing_financial_estimates,new_financial_estimate_df],ignore_index=True)
    updated_comparables = pd.concat([existing_comparable_companies,new_comparables_df],ignore_index=True)

    return updated_income_statement,updated_balace_sheet,updated_cash_flow, updated_finanical_estimates, updated_comparables

def pull_income_statment(target_tickers, API_KEY):

    income_statement_data = []
    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/income-statement?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)
        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue

        data = response.json()

        if isinstance(data,list) & len(data) > 0:
            income_statement_data.extend(data)
    
        
    income_stmt_df = pd.DataFrame(income_statement_data)
    return income_stmt_df


def pull_balance_sheet(target_tickers, API_KEY):

    balance_sheet_data = []
    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)
        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue
        
        data = response.json()

        if isinstance(data,list) & len(data) > 0:
            balance_sheet_data.extend(data)
        
    balance_sheet_df = pd.DataFrame(balance_sheet_data)
    return balance_sheet_df 

def pull_cashflow_statment(target_tickers,API_KEY):

    cashflow_statment_data = [] 
    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/cash-flow-statement?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)
        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue

        data = response.json()
 
        if isinstance(data,list) & len(data) > 0:
            cashflow_statment_data.extend(data)

    cashflow_stmt_df = pd.DataFrame(cashflow_statment_data)
    return cashflow_stmt_df

def pull_finanical_estimates(target_tickers, API_KEY):

    financial_estimate_data = []
    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/analyst-estimates?symbol={i}&period=annual&apikey={API_KEY}'
        response = requests.get(url)

        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue
        
        data = response.json()

        if isinstance(data,list) and len(data) > 0:
            financial_estimate_data.extend(data)
    
    financial_estimate_df = pd.DataFrame(financial_estimate_data)
    return financial_estimate_df

def pull_market_data(ranked_df):
    market_data = []
    for ticker in ranked_df['Symbol']:
        Ticker = yf.Ticker(ticker)
        info = Ticker.info
        last_price = Ticker.fast_info['last_price']
        sector = info.get('sector')
        industry = info.get('industry')
        beta = info.get('beta')
        market_cap = info.get('marketCap')
        dct = {'Ticker':ticker,'LastPrice':last_price, 'Sector':sector, 'Industry':industry, 'Beta':beta, 'MarketCap':market_cap}
        market_data.append(dct)

    market_data_df = pd.DataFrame(market_data)

    return market_data_df

def get_comparable_companies(target_tickers,API_KEY):

    comparable_companies = []

    for i in target_tickers:
        url = f'https://financialmodelingprep.com/stable/stock-peers?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)

        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue

        data = response.json()

        if isinstance(data,list) & (len(data) > 0):
            for peer in data:
                peer['Target Company'] = i

        comparable_companies.extend(data)


    comparables_df = pd.DataFrame(comparable_companies)

    return comparables_df

def pull_multiples(comparables_df):

    multiples_list = []

    for symbol in comparables_df['symbol']:

        symbol = str(symbol).strip().upper()

        if not symbol or symbol == 'NAN':
            continue 
        
        yahoo_symbol = symbol.replace('.','-')

        try:
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            sector = info.get('sector')
            foward_pe = info.get('forwardPE')
            ev_to_ebitda = info.get('enterpriseToEbitda')
            price_to_sales = info.get('priceToSalesTrailing12Months')

            dct = {'symbol':symbol,'Sector':sector,'ForwardPE':foward_pe,'EVtoEBITDA':ev_to_ebitda,'PriceToSales':price_to_sales}
            multiples_list.append(dct)
        
        except Exception as error:
            print(f'Yahoo Failed for {symbol}: {error}')
            continue

    multiples_df = pd.DataFrame(multiples_list)

    return multiples_df

def get_analyst_price_target(ranked_df,API_KEY):

    analyst_prices = []

    for i in ranked_df['Symbol']:
        url = f'https://financialmodelingprep.com/stable/price-target-consensus?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)

        if response.status_code != 200 or response.text.strip() == "":
            print(f'Bad Response {i}: {response.status_code}')
            continue

        data = response.json()

        if isinstance(data,list) and len(data) > 0:
            analyst_prices.extend(data)

    analyst_price_df = pd.DataFrame(analyst_prices)

    return analyst_price_df

def get_analyst_grade(ranked_df,API_KEY):

    analyst_summary = []

    for i in ranked_df['Symbol']:
        url = f'https://financialmodelingprep.com/stable/grades-consensus?symbol={i}&apikey={API_KEY}'
        response = requests.get(url)

        if response.status_code != 200 or response.text.strip() == '':
            print(f'Bad Response {i}: {response.status_code}')
            continue

        data = response.json()

        if isinstance(data,list) and len(data) > 0:
            analyst_summary.extend(data)

    analyst_summary_df = pd.DataFrame(analyst_summary)

    return analyst_summary_df

        
# =========================
# DATA CONSOLIDATION
# =========================            

def save_fmp_data(ratios_df,metrics_df,income_stmt_df,balance_sheet_df,cashflow_stmt_df,financial_estimate_df,market_data_df,comparables_df,multiples_df, updated_unavailable_tickers_df,analyst_price_df,analyst_summary_df):
    path = BASE_PATH + r'\fundamental_data.xlsx'
    with pd.ExcelWriter(path) as writer:
        ratios_df.to_excel(writer,sheet_name = 'Ratios', index=False)
        metrics_df.to_excel(writer, sheet_name = 'Metrics', index=False)
        income_stmt_df.to_excel(writer, sheet_name = 'Income Statement', index=False)
        balance_sheet_df.to_excel(writer, sheet_name = 'Balance Sheet', index=False)
        cashflow_stmt_df.to_excel(writer, sheet_name = 'Cash Flow Statement', index=False)
        financial_estimate_df.to_excel(writer, sheet_name = 'Financial Estimates',index=False)
        market_data_df.to_excel(writer, sheet_name = 'Market Data', index=False)
        comparables_df.to_excel(writer, sheet_name='Comparable Companies', index=False)
        multiples_df.to_excel(writer, sheet_name='Multiples', index=False)
        analyst_price_df.to_excel(writer, sheet_name='Analyst Price Targets', index=False)
        analyst_summary_df.to_excel(writer, sheet_name="Analyst Summary", index=False)

    file_path = BASE_PATH + r'\unavailable_tickers.xlsx'
    updated_unavailable_tickers_df.to_excel(file_path,index=False)


def read_fundamental_data():
    path = BASE_PATH + r'\fundamental_data.xlsx'
    ratios_df = pd.read_excel(path, sheet_name='Ratios')
    metrics_df = pd.read_excel(path, sheet_name='Metrics')
    income_stmt_df = pd.read_excel(path, sheet_name='Income Statement')
    balance_sheet_df = pd.read_excel(path, sheet_name='Balance Sheet')  
    cashflow_stmt_df = pd.read_excel(path, sheet_name='Cash Flow Statement')
    financial_estimate_df = pd.read_excel(path, sheet_name='Financial Estimates')
    market_data_df = pd.read_excel(path,sheet_name='Market Data' )
    comparables_df = pd.read_excel(path,sheet_name='Comparable Companies')
    multiples_df = pd.read_excel(path,sheet_name='Multiples')
    analyst_price_df = pd.read_excel(path, sheet_name='Analyst Price Targets')
    analyst_summary_df = pd.read_excel(path, sheet_name='Analyst Summary')
    return ratios_df, metrics_df, income_stmt_df, balance_sheet_df, cashflow_stmt_df, financial_estimate_df, market_data_df,comparables_df,multiples_df,analyst_price_df,analyst_summary_df



# =========================
# ClEANING FINANCIAL STATEMENT LAYER
# =========================

def clean_income_statement(income_stmt_df, stock):

    income_statement = income_stmt_df.loc[income_stmt_df['symbol'] == stock,['fiscalYear','revenue','costOfRevenue','grossProfit','researchAndDevelopmentExpenses','sellingGeneralAndAdministrativeExpenses','otherExpenses','operatingIncome','ebit','interestExpense','incomeTaxExpense']]
    income_statement.rename(columns = {'researchAndDevelopmentExpenses':'R&D','sellingGeneralAndAdministrativeExpenses':'SG&A','incomeTaxExpense':'TaxExpense','ebit':'EBIT'},inplace=True)
    income_statement = income_statement.set_index('fiscalYear').T.sort_index(axis=1)

    revenue_growth = income_statement.loc['revenue'].pct_change()
    income_statement.loc['%Growth'] = revenue_growth

    gross_margin = income_statement.loc['grossProfit'] / income_statement.loc['revenue']
    income_statement.loc['GrossMargin%'] = gross_margin

    operating_margin = income_statement.loc['operatingIncome'] / income_statement.loc['revenue']
    income_statement.loc['OperatingMargin%'] = operating_margin 

    ebit_margin = income_statement.loc['EBIT'] / income_statement.loc['revenue']
    income_statement.loc['EBITmargin%'] = ebit_margin 

    tax_rate = income_statement.loc['TaxExpense'] / income_statement.loc['EBIT']
    income_statement.loc['TaxRate%'] = tax_rate 

    income_statement.loc['Revenues'] = ''
    income_statement.loc['    FixedCosts'] = ''
    income_statement.loc['    VariableCosts'] = ''
    income_statement.loc['OperatingExpenses&Income'] = ''
    income_statement.loc['    FixedSG&A'] = ''
    income_statement.loc['    VariableSG&A'] = ''
    income_statement.loc[''] = ''
    income_statement.loc[' '] = ''
    income_statement.loc['  '] = ''

    new_order = [' ','Revenues','revenue','%Growth','    FixedCosts','    VariableCosts','costOfRevenue','grossProfit','GrossMargin%','',
                 'OperatingExpenses&Income','R&D','    FixedSG&A','    VariableSG&A','SG&A','otherExpenses','operatingIncome','OperatingMargin%','  ',
                 'EBIT','EBITmargin%','interestExpense','TaxExpense','TaxRate%'
                 ]
    income_statement = income_statement.reindex(new_order)

    pd.options.display.float_format = '{:,.4f}'.format  

    return income_statement

def clean_balance_sheet(balance_sheet_df, income_stmt_df, stock):

    balance_sheet = balance_sheet_df.loc[balance_sheet_df['symbol'] == stock,['fiscalYear','cashAndCashEquivalents','shortTermInvestments','cashAndShortTermInvestments','accountsReceivables','inventory','accountPayables','totalDebt']]
    shares_outstanding = income_stmt_df.loc[income_stmt_df['symbol'] == stock,'weightedAverageShsOutDil'].values[::-1]
    balance_sheet = balance_sheet.set_index('fiscalYear').T.sort_index(axis=1)
    balance_sheet.loc['weightedAverageShsOutDil'] = shares_outstanding
    balance_sheet.loc['netDebt'] = balance_sheet.loc['totalDebt'] - balance_sheet.loc['cashAndShortTermInvestments']
    

    balance_sheet = balance_sheet.astype(float)

    balance_sheet.loc['Cash&ShortTermInvestments'] = ''
    balance_sheet.loc['CurrentAssets'] = ''
    balance_sheet.loc['CurrentLiabilities'] = ''
    balance_sheet.loc['Debt'] = ''
    balance_sheet.loc['DilutedSharesOutstanding'] = ''
    balance_sheet.loc[''] = ''
    balance_sheet.loc[' '] = ''
    balance_sheet.loc['   '] = ''
    balance_sheet.loc['    '] = '' 
    balance_sheet.loc['     '] = ''

    
    new_order = ['','Cash&ShortTermInvestments','cashAndCashEquivalents','shortTermInvestments','cashAndShortTermInvestments',' ','CurrentAssets','accountsReceivables','inventory','   ','CurrentLiabilities','accountPayables','    ','Debt','totalDebt','netDebt','     ','DilutedSharesOutstanding','weightedAverageShsOutDil']
    balance_sheet = balance_sheet.reindex(new_order)

    pd.options.display.float_format = '{:,.4f}'.format 

    return balance_sheet
    
def clean_cash_flow(cashflow_stmt_df, stock):

    cash_flow = cashflow_stmt_df.loc[cashflow_stmt_df['symbol'] == stock,['fiscalYear','depreciationAndAmortization','capitalExpenditure','freeCashFlow']]
    cash_flow = cash_flow.set_index('fiscalYear').T.sort_index(axis=1)

    cash_flow = cash_flow.astype(float)

    cash_flow.loc['CashFlowFromOperatingActivities'] = ''
    cash_flow.loc['CashFlowFromInvestingActivities'] = ''
    cash_flow.loc[''] = ''
    cash_flow.loc[' '] = ''

    new_order = ['','CashFlowFromOperatingActivities','depreciationAndAmortization',' ','CashFlowFromInvestingActivities','capitalExpenditure','freeCashFlow']
    cash_flow = cash_flow.reindex(new_order)
    
    pd.options.display.float_format = '{:,.4f}'.format 

    return cash_flow

def clean_financial_estimates_data(financial_estimate_df,stock):
    finanical_estimates = financial_estimate_df.loc[financial_estimate_df['symbol'] == stock,['date','revenueLow','revenueHigh','revenueAvg','ebitdaHigh','ebitdaAvg','ebitLow','epsAvg','epsHigh',	'epsLow']]

    finanical_estimates = finanical_estimates.set_index('date').T.sort_index(axis=1)

    years = pd.to_datetime(finanical_estimates.columns, errors = 'coerce').year

    finanical_estimates.columns = years

    finanical_estimates.columns = finanical_estimates.columns.astype(int)

    return finanical_estimates


def clean_market_data(market_data_df, stock):

    market_data = market_data_df.loc[market_data_df['Ticker'] == stock,['Sector','Beta','LastPrice','Industry','MarketCap']].T

    pd.options.display.float_format = '{:,.4f}'.format 

    return market_data


# =========================
# FILTER LAYER
# =========================

def sanity_checks(income_statement, balance_sheet, cash_flow, market_data, stock):

    if (market_data.loc['Industry'] == 'Auto Manufacturers').any():
        print(f'⚠️ WARNING: {stock} is in the Automakeres Industry. DCF model not supported.')
        return False
    

    if (market_data.loc['Sector'] == 'Financial Services').any() or (market_data.loc['Sector'] == 'Real Estate').any():
        print(f'⚠️ WARNING: {stock} is a Financial Services company. DCF model not supported.')
        return False
    
    if len(income_statement.columns) < 4 or len(balance_sheet.columns) < 4 or len(cash_flow.columns) < 4:
        print(f'⚠️ WARNING: Not enough historical data for {stock}. Cannot forecast')
        return False
    
    if (income_statement.loc['revenue'] <= 0).any():
        print(f'⚠️ WARNING: Revenue for {stock} is zero or negative. Cannot forecast')
        return False
    
    if (income_statement.loc['grossProfit'] > income_statement.loc['revenue']).any():
        print(f'⚠️ WARNING: Gross Profit for {stock} exceeds Revenue. Cannot forecast')
        return False
    
    if (income_statement.loc['TaxRate%'] > 1.0).any() or (income_statement.loc['TaxRate%'] < 0).any():
        print(f'⚠️ WARNING: Tax Rate for {stock} is outside of expected range (0-100%). Cannot forecast')
        return False
    
    if (balance_sheet.loc['netDebt'].isna()).any():
        print(f'⚠️ WARNING: Net Debt for {stock} is missing. Cannot forecast')
        return False
    
    if (balance_sheet.loc['weightedAverageShsOutDil'].isna()).any() or (balance_sheet.loc['weightedAverageShsOutDil'] <= 0).any():
        print(f'⚠️ WARNING: Diluted Shares Outstanding for {stock} is missing or non-positive. Cannot forecast')
        return False

    return True 

# =========================
# DCF 
# =========================


# =========================
# FORECASTING LAYER 
# =========================


def revenue_schedule(income_statement, financial_estimates, growth_adjustment, terminal_growth):

    last_hist_year = income_statement.columns[-1]
    year_1 = last_hist_year + 1 
    year_2 = last_hist_year + 2
    estimate_forecast_years = [year_1, year_2]
    forecast_years = [estimate_forecast_years[1] + i for i in range(1,4)]

    last_forecast_year = str(estimate_forecast_years[1]) + 'F'

    for year in estimate_forecast_years:
        last_year = income_statement.columns[-1]
        year_f = str(year) + 'F'

        income_statement[year_f] = np.nan
        income_statement.at['revenue',year_f] = financial_estimates.at['revenueAvg',year]
        income_statement.at['%Growth',year_f] = (income_statement.at['revenue',year_f] - income_statement.at['revenue',last_year]) / income_statement.at['revenue',last_year]

    current_rev = income_statement.at['revenue',last_forecast_year]
    current_growth = income_statement.at['%Growth',last_forecast_year]
    base_growth = income_statement.at['%Growth',last_forecast_year] + growth_adjustment

    for idx,year in enumerate(forecast_years, start=1):
        year = str(year) + 'F'
        income_statement[year] = np.nan

        if current_growth > .30:
            decay_factor = .35
        elif current_growth > .15:
            decay_factor = .20
        else:
            decay_factor = .10

        current_growth = terminal_growth + (base_growth - terminal_growth) * ((1 - decay_factor) ** idx)
        income_statement.at['%Growth',year] = current_growth

        current_rev = current_rev * (1 + current_growth)
        income_statement.at['revenue',year] = current_rev

    # Revenue Schedule for Terminal Year
    income_statement['Term'] = np.nan
    income_statement.at['%Growth','Term'] = terminal_growth

    final_forecast_year = f'{forecast_years[-1]}F'
    income_statement.at['revenue','Term'] = income_statement.at['revenue',final_forecast_year] * (1 + terminal_growth)

    return income_statement


def cost_schedule(stock,income_statement, market_data):
    historical_years = [col for col in income_statement.columns if isinstance(col,int)]
    forecast_years = [col for col in income_statement.columns if isinstance(col, str)]
    
    last_hist_year = max(historical_years)

    valid_observable_years = [col for col in income_statement.columns if isinstance(col,int) and col != last_hist_year]

    sector = market_data.loc['Sector'].iloc[0]
    inflation = .02

    base_revenue = income_statement.at['revenue',last_hist_year]
    base_cogs = income_statement.at['costOfRevenue',last_hist_year]

    base_sga = income_statement.at['SG&A',last_hist_year]

    if base_sga == 0:
        base_sga = income_statement.loc['SG&A',valid_observable_years].mean()
    

    # Assumtpions for Operating Levarage Schedule for COGS
    fixed_cogs_ratios = {
        'Technology':.30, 
        'Communication Services':.25, 
        'Healthcare': .15, 
        'Industrials':.05,
        'Consumer Cyclical':.05,
        'Consumer Defensive':.05, 
        'Energy':.05,
        }
    
    fixed_cogs_ratio = fixed_cogs_ratios.get(sector, .05)
    fixed_cogs = base_cogs * fixed_cogs_ratio
    variable_cogs_pct = (base_cogs * ( 1 - fixed_cogs_ratio)) / base_revenue

    # Assumtpions for Operating Levarage Schedule for SG&A
    fixed_sga_ratios = {
        'Technology':.40, 
        'Communication Services':.40, 
        'Healthcare': .60, 
        'Industrials':.40,
        'Consumer Cyclical':.40,
        'Consumer Defensive':.50, 
        'Energy':.50,
        }

    fixed_sga_ratio = fixed_sga_ratios.get(sector,.50)
    fixed_sga = base_sga * fixed_sga_ratio
    variable_sga_pct = (base_sga * (1 - fixed_sga_ratio)) / base_revenue

    for i, year in enumerate(forecast_years,start=1):

        # Forecast COGS Using Operating Leverage Assumptions
        current_inflated_fixed_cogs = fixed_cogs * ((1+ inflation) ** i)
        current_forecast_revenue = income_statement.at['revenue',year]
        current_variable_cogs = current_forecast_revenue * variable_cogs_pct 

        income_statement.at['    FixedCosts',year] = current_inflated_fixed_cogs
        income_statement.at['    VariableCosts',year] = current_variable_cogs
        income_statement.at['costOfRevenue',year] = current_inflated_fixed_cogs + current_variable_cogs

        current_inflated_fixed_sga = fixed_sga * ((1+inflation) ** i)
        current_variable_sga = current_forecast_revenue * variable_sga_pct

        income_statement.at['    FixedSG&A',year] = current_inflated_fixed_sga
        income_statement.at['    VariableSG&A',year] = current_variable_sga
        income_statement.at['SG&A',year] = current_inflated_fixed_sga + current_variable_sga

    return income_statement



def forcast_income_statement(stock,income_statement,market_data):
    historical_years = [col for col in income_statement.columns if isinstance(col,int)]
    forecast_years = [col for col in income_statement.columns if isinstance(col,str)]
    

    # Forcasting assumptions 
    hist_rd_pct = (income_statement.loc['R&D',historical_years] / income_statement.loc['revenue',historical_years]).mean()
    hist_other_pct = (income_statement.loc['otherExpenses',historical_years] / income_statement.loc['revenue',historical_years]).mean()
    hist_tax_rate_mean = income_statement.loc['TaxRate%',historical_years].mean()
    hist_interest_expense_pct = (income_statement.loc['interestExpense',historical_years] / income_statement.loc['revenue',historical_years]).mean()


    for year in forecast_years:

        # Growth and Revenue Calculations
        income_statement.at['grossProfit',year] = income_statement.at['revenue',year] - income_statement.at['costOfRevenue',year]
        income_statement.at['GrossMargin%',year] = income_statement.at['grossProfit',year] / income_statement.at['revenue',year]

        # Operating Expenses Projections
        income_statement.at['R&D',year] = (income_statement.at['revenue',year] * hist_rd_pct)
        income_statement.at['otherExpenses',year] = (income_statement.at['revenue',year] * hist_other_pct)

        # Operating Income and Margin Projections
        income_statement.at['operatingIncome',year] = (income_statement.at['grossProfit',year] - income_statement.at['R&D',year] - income_statement.at['SG&A',year] - income_statement.at['otherExpenses',year])
        income_statement.at['OperatingMargin%',year] = (income_statement.at['operatingIncome',year] / income_statement.at['revenue',year])

        # EBIT, and Taxes Projections
        income_statement.at['EBIT',year] = (income_statement.at['operatingIncome',year])
        income_statement.at['EBITmargin%',year] = (income_statement.at['EBIT',year] / income_statement.at['revenue',year])
        income_statement.at['interestExpense',year] = (income_statement.at['revenue',year] * hist_interest_expense_pct)
        income_statement.at['TaxRate%',year] = hist_tax_rate_mean
        income_statement.at['TaxExpense',year] = income_statement.at['EBIT',year] * hist_tax_rate_mean

        # NOPAT Calculation
        income_statement.at['NOPAT',year] = income_statement.at['EBIT',year] * (1 - hist_tax_rate_mean)

    income_statement.loc['NOPAT',historical_years] = income_statement.loc['EBIT',historical_years] * (1 - hist_tax_rate_mean)

    #Operating Margin Sanity Checkers
    sector = market_data.loc['Sector'].iloc[0]

    sector_om_caps = {
        'Technology':.45,
        'Communication Services':.50,
        'HealthCare':.35,
        'Industrials':.25,
        'Consumer Cyclical':.20,
        'Consumer Defensive':.18,
        'Energy':.22
    }
    om_cap = sector_om_caps.get(sector,.30)
    if income_statement.loc['OperatingMargin%',forecast_years].max() > om_cap:
        income_statement.loc['OperatingMargin%',forecast_years] = income_statement.loc['OperatingMargin%',historical_years].mean()
        income_statement.loc['operatingIncome',forecast_years] = income_statement.loc['OperatingMargin%',forecast_years] * income_statement.loc['revenue',forecast_years]
        income_statement.loc['EBIT',forecast_years] = income_statement.loc['operatingIncome',forecast_years]
        income_statement.loc['NOPAT',forecast_years] = income_statement.loc['operatingIncome',forecast_years] * (1-hist_tax_rate_mean)
    
    return income_statement

def forecast_balance_sheet(balance_sheet,stock):

    return balance_sheet

def working_capital_schedule(income_statement, balance_sheet):
    histroical_years = [col for col in income_statement.columns if isinstance(col,int)]
    forecast_years = [col for col in income_statement.columns if isinstance(col,str)]
    all_years = histroical_years + forecast_years
    days_in_period = 365

    wc_rows = ['DaysInPeriod','Revenue','COGS','','AmountsPerDay','AccountsReceivableDAYS','InventoryDAYS','AccountsPayableDAYS',' ','TotalAmounts',
               'AccountsReceivables','Inventory','AccountsPayable', '  ', 'Networking Capital','CurrentAssets','CurrentLiabilities','Net Working Capital','    ','Cash from Working Capital Items']

    working_capital_df = pd.DataFrame(index=wc_rows,columns=all_years)

    working_capital_df.loc['Revenue'] = income_statement.loc['revenue']
    working_capital_df.loc['COGS'] = income_statement.loc['costOfRevenue']

    # Amounts Per Day
    working_capital_df.loc['AccountsReceivableDAYS',histroical_years] = (balance_sheet.loc['accountsReceivables',histroical_years]/income_statement.loc['revenue',histroical_years]) * days_in_period
    working_capital_df.loc['InventoryDAYS',histroical_years] = (balance_sheet.loc['inventory',histroical_years]/income_statement.loc['costOfRevenue',histroical_years]) * days_in_period
    working_capital_df.loc['AccountsPayableDAYS',histroical_years] = (balance_sheet.loc['accountPayables',histroical_years]/income_statement.loc['costOfRevenue',histroical_years]) * days_in_period

    avg_ar_days = working_capital_df.loc['AccountsReceivableDAYS',histroical_years].mean()
    avg_inventory_days = working_capital_df.loc['InventoryDAYS',histroical_years].mean()
    avg_ap_days = working_capital_df.loc['AccountsPayableDAYS',histroical_years].mean()

    working_capital_df.loc['AccountsReceivableDAYS',forecast_years] = avg_ar_days
    working_capital_df.loc['InventoryDAYS',forecast_years] = avg_inventory_days
    working_capital_df.loc['AccountsPayableDAYS',forecast_years] = avg_ap_days

    # Total Amounts
    working_capital_df.loc['AccountsReceivables',histroical_years] = balance_sheet.loc['accountsReceivables']
    working_capital_df.loc['Inventory',histroical_years] = balance_sheet.loc['inventory'] 
    working_capital_df.loc['AccountsPayable',histroical_years] = balance_sheet.loc['accountPayables']

    working_capital_df.loc['AccountsReceivables',forecast_years] = (working_capital_df.loc['AccountsReceivableDAYS',forecast_years] / days_in_period) * working_capital_df.loc['Revenue',forecast_years]
    working_capital_df.loc['Inventory',forecast_years] = (working_capital_df.loc['InventoryDAYS',forecast_years] / days_in_period) * working_capital_df.loc['COGS',forecast_years]
    working_capital_df.loc['AccountsPayable',forecast_years] = (working_capital_df.loc['AccountsPayableDAYS',forecast_years] / days_in_period) * working_capital_df.loc['COGS',forecast_years]

    # Net Working Capital 
    working_capital_df.loc['CurrentAssets'] = working_capital_df.loc['AccountsReceivables'] + working_capital_df.loc['Inventory']
    working_capital_df.loc['CurrentLiabilities'] = working_capital_df.loc['AccountsPayable']
    working_capital_df.loc['Net Working Capital'] = working_capital_df.loc['CurrentAssets'] - working_capital_df.loc['CurrentLiabilities']

    # Cash from Working Capital Items 
    working_capital_df.loc['Cash from Working Capital Items'] = working_capital_df.loc['Net Working Capital'].diff() * - 1

    return working_capital_df

def forecast_cash_flow_statement(cash_flow, income_statement, stock):   
    income_statement_historical_years = [col for col in income_statement.columns if isinstance(col,int)]
    cash_flow_historical_years = [col for col in cash_flow.columns if isinstance(col,int)]

    if income_statement_historical_years != cash_flow_historical_years:
        cash_flow.columns = income_statement_historical_years

    historical_years = [col for col in cash_flow.columns if isinstance(col,int)]
    forecast_years = [col for col in income_statement.columns if isinstance(col,str)]

    cash_flow.loc['capitalExpenditure'] = abs(cash_flow.loc['capitalExpenditure'])

    avg_da_pct = (cash_flow.loc['depreciationAndAmortization', historical_years] / income_statement.loc['revenue', historical_years]).mean()
    avg_capex_pct = (cash_flow.loc['capitalExpenditure',historical_years] / income_statement.loc['revenue',historical_years]).mean()
    for year in forecast_years:

        # D&A and Capex Projections
        cash_flow.at['depreciationAndAmortization',year] = income_statement.at['revenue',year] * avg_da_pct
        cash_flow.at['capitalExpenditure',year] = income_statement.at['revenue',year] * avg_capex_pct

    return cash_flow


# =========================
# DCF VALUTATION LAYER
# =========================

def calculate_fcf(income_statement, cash_flow, working_capital_df, stock):

    forecast_years = [col for col in income_statement.columns if isinstance(col,str)]
    historical_years = [col for col in income_statement.columns if isinstance(col,int)]
    all_years = historical_years + forecast_years

    NOPAT = income_statement.loc['NOPAT',all_years]
    depreciationAndAmortization = cash_flow.loc['depreciationAndAmortization',all_years]
    capitalExpenditure = cash_flow.loc['capitalExpenditure',all_years]
    cashFromWorkingCapital = working_capital_df.loc['Cash from Working Capital Items',all_years]

    valuation_df = NOPAT.to_frame().T
    valuation_df.loc['D&A'] = depreciationAndAmortization
    valuation_df.loc['Capex'] = capitalExpenditure
    valuation_df.loc['Cash from Working Capital Items'] = cashFromWorkingCapital
    valuation_df.loc['FCF'] = valuation_df.loc['NOPAT'] + valuation_df.loc['D&A'] - valuation_df.loc['Capex'] + valuation_df.loc['Cash from Working Capital Items']

    valuation_df.loc['FCF Margin%'] = valuation_df.loc['FCF'] / income_statement.loc['revenue',all_years]
    valuation_df.loc['FCF Conversion'] = valuation_df.loc['FCF'] / valuation_df.loc['NOPAT']
    valuation_df.loc[''] = '' 
    valuation_df.loc['Capex/Revenue'] = valuation_df.loc['Capex'] / income_statement.loc['revenue'] * 100
    valuation_df.loc['Capex/D&A'] = valuation_df.loc['Capex'] / valuation_df.loc['D&A'] * 100
    valuation_df.loc['D&A/Revenue'] = valuation_df.loc['D&A'] / income_statement.loc['revenue'] * 100

    return valuation_df


def calculate_WACC(income_statement, balance_sheet, market_data, stock, wacc_adjustment):
    historical_years = [col for col in income_statement.columns if isinstance(col,int)]

    # Calculate Cost Of Equity 

    tnx = yf.Ticker('^TNX')
    raw_yield = tnx.fast_info['last_price']
    try:
        risk_free_rate = raw_yield/100

    except:
        risk_free_rate = 0.04

    beta = market_data.loc['Beta'].iloc[0]
    if pd.isna(beta):
        beta = 1

    equity_risk_premium = 0.055

    cost_of_equity = risk_free_rate + beta * equity_risk_premium

    # Capital Structure 
    market_value_of_equity = market_data.loc['LastPrice'].iloc[0] * balance_sheet.loc['weightedAverageShsOutDil'].iloc[-1]
    market_value_of_debt = balance_sheet.loc['totalDebt'].iloc[-1]

    e_v = market_value_of_equity / (market_value_of_equity + market_value_of_debt)
    d_v = market_value_of_debt / (market_value_of_equity + market_value_of_debt)

    # After Tax Cost of Debt
    interest_expense = abs(income_statement.at['interestExpense',historical_years[-1]])
    tax_rate = income_statement.at['TaxRate%',historical_years[-1]]

    if market_value_of_debt > 0:
        cost_of_debt = interest_expense / market_value_of_debt
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
    else:
        cost_of_debt = 0
        after_tax_cost_of_debt = 0

    # Calculate WACC
    WACC = ((e_v * cost_of_equity) + (d_v * after_tax_cost_of_debt)) + wacc_adjustment

    WACC = max(WACC, 0.080) 

    return WACC

def terminal_value_perpetuity(valuation_df,balance_sheet,income_statement, WACC, stock, terminal_growth):
    
    forecast_years = [col for col in income_statement.columns if isinstance(col,str)]
    test_forecast_years = [col for col in income_statement.columns if isinstance(col,str) and col.endswith('F')]
    last_forecast_year = test_forecast_years[-1]

    discount_factors = []
    pv_cash_flows = []

    # PV of Forecasted Free Cash Flows
    explicit_forecast_years = len(forecast_years[:-1])

    for year,idx in enumerate(range(explicit_forecast_years), start=1):

        discount_factor =  1 / ((1+WACC) ** year)
        discount_factors.append(discount_factor)

        #Calculate Present Value of Future Free Cash Flows
        pv_of_fcf = valuation_df.loc['FCF',forecast_years[idx]] * discount_factor
        pv_cash_flows.append(pv_of_fcf)

    # PV of Terminal Value
    terminal_value = valuation_df.at['FCF', 'Term'] / (WACC - terminal_growth)

    pv_of_terminal_value = terminal_value / ((1 + WACC) ** explicit_forecast_years)

    discount_factors.append(1 / ((1 + WACC) ** explicit_forecast_years))
    pv_cash_flows.append(pv_of_terminal_value)

    valuation_df.loc['DiscountFactor',forecast_years] = discount_factors
    valuation_df.loc['PV_of_FCF',forecast_years] = pv_cash_flows

    # Calculate Enterprise Value, Equity Value and Intrinsic Value Per Share
    terminal_ebitda = income_statement.at['EBIT',last_forecast_year] + valuation_df.at['D&A',last_forecast_year]

    enterprise_value = valuation_df.loc['PV_of_FCF',forecast_years].sum()
    equity_value = enterprise_value - balance_sheet.loc['netDebt'].iloc[-1]
    intrinsic_value_perpetuity = equity_value / balance_sheet.loc['weightedAverageShsOutDil'].iloc[-1]
    terminal_enterprise_value = pv_of_terminal_value / enterprise_value

    return intrinsic_value_perpetuity, terminal_value, terminal_ebitda, terminal_enterprise_value

def terminal_value_exit_multiple(multiples_df,stock,market_data_df,market_data,valuation_df,metrics_df,income_statement,balance_sheet,WACC,exit_multiple_factor):

    # Create dataframe using the comparables EV/EBITDA and target stocks
    market_data_df_copy = market_data_df.copy()
    market_data_df_copy = market_data_df_copy.rename(columns={'Ticker':'symbol'})

    exit_multiple_df = pd.merge(metrics_df[['symbol','evToEBITDATTM']],market_data_df_copy[['symbol','Sector']],on='symbol',how='inner')

    multiples_df_copy = multiples_df.copy()
    multiples_df_copy = multiples_df_copy.rename(columns={'EVtoEBITDA':'evToEBITDATTM'})

    exit_multiple_df = pd.concat([exit_multiple_df,multiples_df_copy[['symbol','Sector','evToEBITDATTM']]],ignore_index=True,axis=0)

    clean_exit_multiple_df = exit_multiple_df[(exit_multiple_df['evToEBITDATTM'] > 0) & (exit_multiple_df['evToEBITDATTM'] < 30)]


    forecast_years = [col for col in income_statement.columns if isinstance(col,str) and col.endswith('F') ]
    last_forecast_year = forecast_years[-1]

    sector = market_data.loc['Sector'].iloc[-1]

    # Using Sector Median EV/EBITDA For the exit multiple 
    sector_exit_multiples = clean_exit_multiple_df.groupby('Sector')['evToEBITDATTM'].median().to_dict()
    sector_multiple = sector_exit_multiples.get(sector,.10) + exit_multiple_factor

    terminal_ebitda = income_statement.at['EBIT',last_forecast_year] + valuation_df.at['D&A',last_forecast_year]

    # Calculating terminal value using exit multiples
    terminal_value = terminal_ebitda * sector_multiple

    # Calculating enterprise value by adding terminal value + sum of fcfs
    pv_terminal_value = terminal_value / ((1 + WACC) ** len(forecast_years))
    sum_of_fcf = valuation_df.loc['PV_of_FCF',forecast_years].sum()
    enterprise_value = pv_terminal_value + sum_of_fcf

    # Equity Value then Intrinsic Value per Share
    net_debt = balance_sheet.loc['netDebt'].iloc[-1]
    equity_value = enterprise_value - net_debt
    intrinsic_value_per_share_ext = equity_value / balance_sheet.loc['weightedAverageShsOutDil'].iloc[-1]   
    terminal_enterprise_value = pv_terminal_value / enterprise_value
              
    return intrinsic_value_per_share_ext, sector_exit_multiples, terminal_value, terminal_ebitda, terminal_enterprise_value

# =========================
# COMPARABLE COMPANY ANALYSIS
# =========================

def clean_comps_data(comparables_df,multiples_df):

    COMPS_df = pd.merge(comparables_df,multiples_df,how='inner',on='symbol')
    COMPS_df = COMPS_df.rename(columns={'symbol':'peer'})

    comps_df = COMPS_df.copy()

    multiples_cols = ['ForwardPE','EVtoEBITDA','PriceToSales']

    for col in multiples_cols:
        comps_df[col] = pd.to_numeric(comps_df[col],errors='coerce')

        comps_df.loc[~((comps_df['ForwardPE'] > 0) & (comps_df['ForwardPE'] < 100)),'ForwardPE'] = np.nan

        comps_df.loc[~((comps_df['EVtoEBITDA'] > 0) & (comps_df['EVtoEBITDA'] < 100)), 'EVtoEBITDA'] = np.nan

        comps_df.loc[~((comps_df['PriceToSales'] > 0) & (comps_df['PriceToSales'] < 100)), 'PriceToSales'] = np.nan

    return comps_df

def get_peer_medians(comps_df):

    peer_medians = comps_df.groupby('Target Company')[['ForwardPE','EVtoEBITDA','PriceToSales']].median()

    return peer_medians

def apply_to_target(peer_medians,financial_estimates,income_statement,balance_sheet):
    
    historical_years = [col for col in income_statement.columns if isinstance(col,int)]
    forecast_years = [col for col in income_statement.columns if isinstance(col,str)]
    first_forecast_year = forecast_years[0]
    last_historical_year = historical_years[-1]
    first_forecast_year_datetime = pd.to_datetime(first_forecast_year.strip('F')).year

    median_ev_to_ebitda = peer_medians['EVtoEBITDA'].iloc[0]
    median_forward_pe = peer_medians['ForwardPE'].iloc[0]
    median_price_to_sales = peer_medians['PriceToSales'].iloc[0]

    first_forecast_EBITDA = financial_estimates.loc['ebitdaAvg',first_forecast_year_datetime]
    first_forecast_eps = financial_estimates.loc['epsAvg',first_forecast_year_datetime]
    first_forecast_revenue = income_statement.loc['revenue',first_forecast_year]

    revenue_per_share = first_forecast_revenue / balance_sheet.loc['weightedAverageShsOutDil',last_historical_year]
    enterprise_value = median_ev_to_ebitda * first_forecast_EBITDA
    equity_value = enterprise_value - balance_sheet.loc['netDebt',last_historical_year]

    intrinsic_value_comps_ev_to_ebitda = equity_value / balance_sheet.loc['weightedAverageShsOutDil',last_historical_year]
    intrinsic_value_comps_forward_pe = median_forward_pe * first_forecast_eps
    intrinsic_value_comps_price_to_sales = median_price_to_sales * revenue_per_share

    return intrinsic_value_comps_ev_to_ebitda,intrinsic_value_comps_forward_pe

# =========================
# RUN VALUATION ENGINE
# =========================

def run_valuation_engine(ranked_df,growth_adjustment=0,terminal_growth=0.025,wacc_adjustment=0,exit_multiple_factor=0,sensitivity_ticker = 'ADBE'):
    ratios_df, metrics_df, income_stmt_df, balance_sheet_df, cashflow_stmt_df, financial_estimate_df, market_data_df,comparables_df,multiples_df,analyst_price_df,analyst_summary_df = read_fundamental_data()

    intrinsic_values = []
    comps_values = []
    checking_margins = []
    checking_multiples = []

    for stock in ranked_df['Symbol']:

        # Financial Statements
        income_statement = clean_income_statement(income_stmt_df, stock)
        balance_sheet = clean_balance_sheet(balance_sheet_df, income_stmt_df,stock)
        cash_flow = clean_cash_flow(cashflow_stmt_df, stock)
        financial_estimates = clean_financial_estimates_data(financial_estimate_df,stock)
        market_data = clean_market_data(market_data_df, stock)
        if not sanity_checks(income_statement, balance_sheet, cash_flow, market_data, stock):
            continue

        # Forecasting
        income_statement = revenue_schedule(income_statement, financial_estimates, growth_adjustment=growth_adjustment, terminal_growth=terminal_growth)
        income_statement = cost_schedule(stock,income_statement, market_data)
        income_statement = forcast_income_statement(stock,income_statement,market_data)
        balance_sheet = forecast_balance_sheet(balance_sheet,stock)
        working_capital_df = working_capital_schedule(income_statement,balance_sheet)
        cash_flow = forecast_cash_flow_statement(cash_flow,income_statement,stock)

        # DCF Valuation
        valuation_df = calculate_fcf(income_statement, cash_flow, working_capital_df, stock)
        WACC =  calculate_WACC(income_statement, balance_sheet, market_data,stock,wacc_adjustment=wacc_adjustment)
        intrinsic_value_perpetuity, terminal_value, terminal_ebitda, terminal_enterprise_value = terminal_value_perpetuity(valuation_df,balance_sheet,income_statement,WACC,stock,terminal_growth=terminal_growth)
        intrinsic_value_exit_multiple, sector_exit_multiles, terminal_value_ext, terminal_ebitda_ext, terminal_enterprise_value_ext = terminal_value_exit_multiple(multiples_df,stock,market_data_df,market_data,valuation_df,metrics_df,income_statement, balance_sheet, WACC, exit_multiple_factor=exit_multiple_factor)
        

        # COMPS Valuation
        comps_df = clean_comps_data(comparables_df,multiples_df)
        peer_medians = get_peer_medians(comps_df)
        intrinsic_value_comps_ev_to_ebitda,intrinsic_value_comps_forward_pe = apply_to_target(peer_medians, financial_estimates,income_statement,balance_sheet)

        # DCF Intrinsic Values
        dct_intrinsic_values = {'Ticker':stock,'IntrinsicValuePerpetuity':intrinsic_value_perpetuity,
                                    'IntrinsicValueExitMultiple':intrinsic_value_exit_multiple}
        
        # COMPS Analysis Values                            
        dct_comps_values = {'Ticker':stock,'COMPSevEBITDA':intrinsic_value_comps_ev_to_ebitda,
                            'COMPSFrwdPE':intrinsic_value_comps_forward_pe}
        
        # Data Checking
        dct_checking_margins = {'Ticker':stock,'GrossMargin%2025':income_statement.at['GrossMargin%',2025],
                 'GrossMargin%2030':income_statement.at['GrossMargin%','2030F'],
                 'OperatingMargin2025%':income_statement.at['OperatingMargin%',2025],
                 'OperatingMargin2030%':income_statement.at['OperatingMargin%','2030F']
                 }
        
        dct_checking_multiples = {'Ticker':stock,'Terminal Value Perpetuity':terminal_value,'Perpetuity Price':intrinsic_value_perpetuity,
                                  'Terminal Value Exit Multiple':terminal_value_ext,'Exit Multiple Price':intrinsic_value_exit_multiple,
                                  'Perpetuity EBITDA':terminal_ebitda, 'Exit EBITDA':terminal_ebitda_ext, 'Perpetuity Terminal/Enterprise':terminal_enterprise_value, 'Exit Terminal/Enterprise':terminal_enterprise_value_ext
                                  }
        

        intrinsic_values.append(dct_intrinsic_values)
        comps_values.append(dct_comps_values)
        checking_margins.append(dct_checking_margins)
        checking_multiples.append(dct_checking_multiples)


        # Sensitivity Analysis 
        if stock == sensitivity_ticker:
            sensitivity_inputs = {'valuation_df':valuation_df, 'balance_sheet':balance_sheet, 
                                  'income_statement':income_statement, 'WACC':WACC}
     
    
    intrinsic_values_df = pd.DataFrame(intrinsic_values)
    comps_values_df = pd.DataFrame(comps_values)
    checking_multiples_df = pd.DataFrame(checking_multiples)

    intrinsic_values_df = intrinsic_values_df.set_index('Ticker')
    comps_values_df['COMPSaverage'] = comps_values_df[['COMPSevEBITDA','COMPSFrwdPE']].mean(axis=1)

    comps_values_df = comps_values_df.set_index('Ticker')
    comps_average = comps_values_df['COMPSaverage']
    
    checking_values_df = pd.DataFrame(checking_margins)
    checking_values_df = checking_values_df.set_index('Ticker')

    return intrinsic_values_df, sensitivity_inputs, comps_average, checking_values_df, sector_exit_multiles, checking_multiples_df

# =========================
# SENSITIVITY ANALYSIS 
# =========================

def sensitivity_analysis(ranked_df, comps_average):
    bear_df, _, _, _, _, _= run_valuation_engine(ranked_df,growth_adjustment=-0.02,terminal_growth=0.02,wacc_adjustment=0.01,exit_multiple_factor=0)
    base_df, _, _, _, _, _ = run_valuation_engine(ranked_df,growth_adjustment=0,terminal_growth=0.025,wacc_adjustment=0.00,exit_multiple_factor=0)
    bull_df, _, _, _, _, _= run_valuation_engine(ranked_df,growth_adjustment=0.02,terminal_growth=0.03,wacc_adjustment=-0.01,exit_multiple_factor=0)

    intrinsic_values_df = pd.concat([bear_df,base_df,bull_df,comps_average],axis=1)

    intrinsic_values_df.columns = ['BearValuePerpetuity','BearValueExitMultiple','BaseValuePerpetuity','BaseValueExitMultiple','BullValuePerpetuity','BullValueExitMultiple','COMPSaverage']
    intrinsic_values_df['BearAverage'] = (intrinsic_values_df['BearValuePerpetuity'] + intrinsic_values_df['BearValueExitMultiple']) / 2
    intrinsic_values_df['BaseAverage'] = (intrinsic_values_df['BaseValuePerpetuity'] + intrinsic_values_df['BaseValueExitMultiple']) / 2
    intrinsic_values_df['BullAverage'] = (intrinsic_values_df['BullValuePerpetuity'] + intrinsic_values_df['BullValueExitMultiple']) / 2

    target_columns = [
'BearValuePerpetuity',
'BearValueExitMultiple',
'BearAverage',

'BaseValuePerpetuity',
'BaseValueExitMultiple',
'BaseAverage',

'BullValuePerpetuity',
'BullValueExitMultiple',
'BullAverage',
'COMPSaverage'
]
    intrinsic_values_df = intrinsic_values_df.reindex(columns=target_columns)


    return intrinsic_values_df


def sensitivity_matrix(valuation_df,balance_sheet,income_statement,WACC,sensitivity_ticker):
    base_wacc = WACC
    wacc_range = [base_wacc - 0.01,base_wacc - 0.005,base_wacc,base_wacc + 0.005,base_wacc + 0.01]
    terminal_growth_range = [0.02,0.025,0.03,0.035,0.04]

    sensitivity_df = pd.DataFrame(index=wacc_range,columns=terminal_growth_range)

    for wacc in wacc_range: 

        for terminalgrowth in terminal_growth_range:

            intrinsic_value = terminal_value_perpetuity(valuation_df,balance_sheet,income_statement, wacc, terminalgrowth)
            sensitivity_df.loc[wacc,terminalgrowth] = intrinsic_value

    plot_df = sensitivity_df.copy()
    plot_df = plot_df.apply(pd.to_numeric,errors='coerce')
    plot_df = plot_df.fillna(0)
    plot_df.index = [f'{w*100:.1f}%' for w in plot_df.index]
    plot_df.columns = [f'{w*100:.1f}' for w in plot_df.columns]

    plt.figure(figsize=(8,6))
    sns.heatmap(plot_df, annot=True,fmt=".2f", cmap="RdYlGn",cbar_kws={'label': 'Intrinsic Value'})

    plt.title(f'Sensitivity Matrix - {sensitivity_ticker}')
    plt.xlabel('Terminal Growth Rate')
    plt.ylabel('WACC')
    plt.tight_layout()
    plt.show()

    # print()
    # print(f'Sensitivity Matrix - {sensitivity_ticker}')
    # print(plot_df)

# =========================
# EFFICIENT FRONTIER
# =========================

def get_mpt_data(research_output_df):
    tickers = research_output_df.index.to_list()
    start_date = '2022-01-01'
    historical_price_data = yf.download(tickers, start=start_date)['Close'].pct_change().dropna()
    cov_matrix = historical_price_data.cov() * 252
    expected_returns = historical_price_data.mean() * 252
    tnx = yf.Ticker('^TNX')
    raw_yield = tnx.fast_info['last_price']
    risk_free_rate = raw_yield / 100
    return cov_matrix,expected_returns, risk_free_rate

def get_weights(research_output_df):
    random_weights = np.random.rand(len(research_output_df))
    total_random_weights = random_weights.sum()
    weights = (random_weights/total_random_weights)

    return weights

def negative_sharpe(weights, cov_matrix, expected_returns, risk_free_rate):
    portfolio_return = np.dot(weights,expected_returns)
    portfolio_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
    sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
    return -sharpe

def optimize_max_sharpe(cov_matrix,expected_returns,risk_free_rate):
    num_stocks = len(expected_returns)
    constraints = ({'type':'eq','fun': lambda weights: np.sum(weights) - 1})
    bounds = tuple((0,0.10) for _ in range(num_stocks))
    initial_guess = np.array([1 / num_stocks] * num_stocks) 
    optimized_results = minimize(negative_sharpe,initial_guess,args=(cov_matrix,expected_returns,risk_free_rate),method='SLSQP',bounds=bounds,constraints=constraints)
    if not optimized_results.success:
        print(optimized_results.message)

    optimized_weights = optimized_results.x
    
    optimal_return = np.dot(optimized_weights,expected_returns)
    optimal_volatility = np.sqrt(optimized_weights.T @ cov_matrix @ optimized_weights)

    optimal_sharpe = (optimal_return - risk_free_rate) / optimal_volatility
    optimal_weights = pd.Series(optimized_weights,index = expected_returns.index)
    
    
    return optimal_sharpe,optimal_weights,optimal_return,optimal_volatility


# =========================
# VALUATION SUMMARY
# =========================

def analyst_additions(analyst_price_df,analyst_summary_df):
    analyst_price_df = analyst_price_df.set_index('symbol')
    analyst_summary_df = analyst_summary_df.set_index('symbol')

    analyst_df = pd.merge(analyst_summary_df,analyst_price_df,on='symbol',how='inner')
    analyst_df = analyst_df[['consensus','targetConsensus']]

    return analyst_df

def valuation_summary(market_data_df,intrinsic_values_df,analyst_df):

    ticker = yf.Ticker('JPY=X')
    jpy_rate = ticker.history(period="1d")['Close'].iloc[-1]

    cols = ['BearValuePerpetuity','BearValueExitMultiple','BearAverage','BaseValuePerpetuity','BaseValueExitMultiple','BaseAverage','BullValuePerpetuity','BullValueExitMultiple','BullAverage','COMPSaverage']

    intrinsic_values_df.loc['SONY', cols] = (intrinsic_values_df.loc['SONY', cols] / jpy_rate)
    analyst_df.loc['SONY','targetConsensus'] = (analyst_df.loc['SONY','targetConsensus'] / jpy_rate)
    

    market_data_df.set_index('Ticker',inplace=True)
    research_output_df = pd.merge(market_data_df,intrinsic_values_df,on ='Ticker', how='inner')
    research_output_df['Bear%'] = (research_output_df['BearAverage'] / research_output_df['LastPrice'] - 1)
    research_output_df['Base%'] = (research_output_df['BaseAverage'] / research_output_df['LastPrice'] - 1)
    research_output_df['Bull%'] = (research_output_df['BullAverage'] / research_output_df['LastPrice'] - 1)
    research_output_df['COMPS%'] = (research_output_df['COMPSaverage'] / research_output_df['LastPrice'] - 1)
    research_output_df['MarginOfSafety'] = (research_output_df['BaseAverage'] / research_output_df['LastPrice'] -1 ) 
    research_output_df = research_output_df.sort_values('Base%',ascending=False)

    positive_return_filter = (research_output_df['Bull%'] > 0) 
    optimized_universe = research_output_df[positive_return_filter]

    analyst_df = analyst_df.rename_axis('Ticker')

    research_output_df = pd.merge(research_output_df,analyst_df,on='Ticker',how='inner')

    print(research_output_df)

    return research_output_df, optimized_universe

# =========================
# DATA VALIDATION
# =========================

def checking_margins(checking_values_df):
    checking_values_df['Gross Margin Change'] = checking_values_df['GrossMargin%2030'] - checking_values_df['GrossMargin%2025']
    checking_values_df['Operating Margin Change'] = checking_values_df['OperatingMargin2030%'] - checking_values_df['OperatingMargin2025%']

    new_columns = ['GrossMargin%2025','GrossMargin%2030','Gross Margin Change','OperatingMargin2025%','OperatingMargin2030%','Operating Margin Change']

    checking_values_df = checking_values_df.reindex(columns=new_columns)

    print(checking_values_df)

def checking_valuation_multiples(metrics_df, market_data_df, sector_exit_multiples, checking_multiples_df):
    ttm_ev_ebitda = metrics_df[['symbol','evToEBITDATTM']]
    ttm_ev_ebitda = ttm_ev_ebitda.set_index('symbol')
    ebitda_sector_df = pd.merge(ttm_ev_ebitda,market_data_df['Sector'],left_index=True,right_index=True)

    ebitda_sector_df['SectorMedian'] = ebitda_sector_df['Sector'].map(sector_exit_multiples)

    new_columns = ['Sector','evToEBITDATTM','SectorMedian']
    ebitda_sector_df = ebitda_sector_df.reindex(columns=new_columns)
    checking_multiples_df = checking_multiples_df.set_index('Ticker')
    checking_multiples = pd.merge(ebitda_sector_df,checking_multiples_df,left_index=True,right_index=True)
    checking_multiples['Implied Perpetuity EV/EBITDA'] = (checking_multiples['Terminal Value Perpetuity'] / checking_multiples['Perpetuity EBITDA'])
    checking_multiples['Terminal Values % Difference'] = (checking_multiples['Terminal Value Exit Multiple'] / checking_multiples['Terminal Value Perpetuity']) - 1 
    checking_multiples = checking_multiples.drop(columns=['Perpetuity EBITDA','Exit EBITDA'])
    new_columns = ['Sector','evToEBITDATTM','SectorMedian','Implied Perpetuity EV/EBITDA','Terminal Value Perpetuity',
                   'Terminal Value Exit Multiple','Terminal Values % Difference','Perpetuity Terminal/Enterprise','Exit Terminal/Enterprise','Perpetuity Price','Exit Multiple Price']
    checking_multiples = checking_multiples.reindex(columns=new_columns)
    checking_multiples['Current EV/EBITDA Difference'] = abs(checking_multiples['evToEBITDATTM'] / checking_multiples['SectorMedian'] - 1)
    checking_multiples['Implied Perpetuity Difference'] = abs(checking_multiples['Implied Perpetuity EV/EBITDA'] / checking_multiples['evToEBITDATTM'] - 1 ) 
    checking_multiples['Exit vs Perpetuity Difference'] = abs((checking_multiples['Exit Multiple Price'] / checking_multiples['Perpetuity Price']) - 1)

    # Status Column 
    current_ev_ebitda_conditions = [
        (checking_multiples['Current EV/EBITDA Difference'] <= .25),
        (checking_multiples['Current EV/EBITDA Difference'].between(.25,.50,inclusive='right')),
        (checking_multiples['Current EV/EBITDA Difference'] > .50)
    ]
    current_ev_ebitda_points = [0,10,20]
    checking_multiples['evToEBITDATTM Points'] = np.select(current_ev_ebitda_conditions,current_ev_ebitda_points,default=np.nan)

    implied_perpetuity_ev_ebitda_conditions = [
        (checking_multiples['Implied Perpetuity Difference'] <= .25),
        (checking_multiples['Implied Perpetuity Difference'].between(.25,.50,inclusive='right')),
        (checking_multiples['Implied Perpetuity Difference'] > .50)
    ]

    implied_perpetuity_ev_ebitda_points = [0,10,20]
    checking_multiples['Implied Perpetuity EV/EBITDA Points'] = np.select(implied_perpetuity_ev_ebitda_conditions,implied_perpetuity_ev_ebitda_points,default=np.nan)

    exit_vs_perpetuity_price_conditions = [
        (checking_multiples['Exit vs Perpetuity Difference'] <= .25),
        (checking_multiples['Exit vs Perpetuity Difference'].between(.25,.50,inclusive='right')),
        (checking_multiples['Exit vs Perpetuity Difference'] > .50)
    ]
    exit_vs_perpetuity_price_points = [0,10,20]
    checking_multiples['ExitVsPerp Points'] = np.select(exit_vs_perpetuity_price_conditions,exit_vs_perpetuity_price_points,default=np.nan)

    terminal_enterprise_value_conditions = [
        (checking_multiples['Perpetuity Terminal/Enterprise'].between(.65,.85)),
        (checking_multiples['Perpetuity Terminal/Enterprise'].between(0.55,0.65, inclusive='left')) | (checking_multiples['Perpetuity Terminal/Enterprise'].between(0.85,0.90, inclusive='right')), 
        (checking_multiples['Perpetuity Terminal/Enterprise'] < .55) | (checking_multiples['Perpetuity Terminal/Enterprise'] > .90)
    ]

    terminal_enterprise_points = [0,10,20]
    checking_multiples['Terminal To Enterprise Points'] = np.select(terminal_enterprise_value_conditions,terminal_enterprise_points,default=np.nan)

    checking_multiples['StatusPoints'] = checking_multiples['evToEBITDATTM Points'] + checking_multiples['Implied Perpetuity EV/EBITDA Points'] + checking_multiples['ExitVsPerp Points'] + checking_multiples['Terminal To Enterprise Points']
    
    status_point_conditions = [
        (checking_multiples['StatusPoints'] <= 20),
        (checking_multiples['StatusPoints'].between(21,50)),
        (checking_multiples['StatusPoints'] > 51)
    ]
    status_point_labels = ['Good','Review','Investigate']
    checking_multiples['StatusLabel'] = np.select(status_point_conditions,status_point_labels,default='Unknown')

    checking_multiples = checking_multiples.drop(columns=['Current EV/EBITDA Difference','Implied Perpetuity Difference','Exit vs Perpetuity Difference','evToEBITDATTM Points','Implied Perpetuity EV/EBITDA Points','ExitVsPerp Points','Terminal To Enterprise Points','StatusPoints'])
    print(checking_multiples)


# =========================
# OUTPUT LAYER 
# =========================
def show_ranked_stocks(ranked_df):
    ranked_df.index = range(len(ranked_df))
    print(
        f'{'Rank':<3}{'Ticker':>10}{'Score%':>11}{'Points':>11}'
        f'{'PEG':>8}'
        f'{'P/E':>9}{'P/FCF':>12}{'EV/EBITDA':>12}{'FCFYield':>12}'
        f'{'ROE':>8}{'ROIC':>12}{'GrossMgn%':>15}{'OpMgn%':>11}{'NetMgn%':>13}'
        f'{'D/E':>10}{'Current':>11}{'NetDebtToEBITDA':>20}')
    
    print('-' * 200)

    for row in ranked_df.itertuples():
        print(
        f'{row.Index:<3}{row.Symbol:>10}{row.ScorePct * 100:>11.2f}%{row.TotalPoints:>11.2f}'
        f'{row.FowardPriceToEarningsGrowth:>9.2f}'
        f'{row.PriceToEarnings:>10.2f}{row.PriceToFCF:>10.2f}{row.EnterpriseValueToEBITDA:>10.2f}{row.FCFYield* 100:>12.2f}%'
        f'{row.ROE * 100:>10.2f}%{row.ROIC * 100:>10.2f}%{row.GrossMargin * 100:>11.2f}%{row.OperatingMargin * 100:>12.2f}%{row.NetProfitMargin * 100:>12.2f}%'
        f'{row.DebtToEquity:>10.2f}{row.CurrentRatio:>10.2f}{row.NetDebtToEbitda:>15.2f}')

def show_valuation_report(research_output_df):
    print(research_output_df)
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[33m'
    RESET = '\033[0m'

    print(
        f'{'Ticker':<5} {'BearValue':>13} {'BaseValue':>13}'
        f'{'BullValue':>14} {'COMPSAverage':>13} {'LastPrice':>12}{'Sector':>20} {'Beta':>15}'
        f'{'Bear Return':>15} {'Base Return':>12} {'Bull Return':>12} {'COMPS Return':>13}'
        f'{'WallStreet Price Target':>25} {'Wall Street Consensus':>22}'
        )
    
    print('-' * 215)

    for row in research_output_df.itertuples():
        bear_diff_color = RED if row[16] < 0 else GREEN if row[16] > 0 else RESET
        base_diff_color = RED if row[17] < 0 else GREEN if row[17] > 0 else RESET
        bull_diff_color = RED if row[18] < 0 else GREEN if row[18] > 0 else RESET
        comps_dff_color = RED if row[19] < 0 else GREEN if row[19] > 0 else RESET
        wall_street_color = YELLOW if row[21] == 'Hold' else GREEN if row[21] == 'Buy' else RESET

        print(
            f'{row.Index:<5} {f'${row.BearAverage:,.2f}':>13} {f'${row.BaseAverage:,.2f}':>13} {f'${row.BullAverage:,.2f}':>13} {f'${row.COMPSaverage:,.2f}':>13} {f'${row.LastPrice:,.2f}':>13}'
            f'{row.Sector:>25} {row.Beta:>10}'
            f'{bear_diff_color}{row[16] * 100:>12.2f}%{RESET} {base_diff_color}{row[17] * 100 :>11.2F}%{RESET} {bull_diff_color}{row[18] * 100:>10.2f}%{RESET} {comps_dff_color}{row[19] * 100:>11.2f}%{RESET}'
            f'{row.targetConsensus:>23,.2f} {wall_street_color}{row.consensus:>17}{RESET}'
        )

def show_efficient_frontier(optimal_sharpe,optimal_weights,optimal_return,optimal_volatility):
    print('Efficient Frontier')
    print('-' * 20)
    print(f'{'Ticker':<15} {'Weight':>11}')
    print('-' * 35)
    for idx,valv in optimal_weights.items():
        print(f'{idx:<15} {valv * 100:>10.2f}%')

    print()

    print('Efficient Frontier Summary')
    print('-' * 35)
    print(f'{'Optimal Return:':<20} {optimal_return * 100:>10.2f}%')
    print(f'{'Optimal Volatility:':<20} {optimal_volatility * 100:>10.2f}%')
    print(f'{'Optimal Sharpe:':<20} {optimal_sharpe:>11.2f}')      


# =========================
# EXECUTION LAYER
# =========================

def execution(refresh=False):
    stock_universe = get_stock_universe()
    existing_ratios_df, existing_metrics_df, existing_tickers, existing_unavaialble_tickers_df, existing_unavaialble_tickers = load_existing_data()
    existing_income_statement, existing_balance_sheet, existing_cash_flow, existing_financial_estimates, existing_comparable_companies = pull_existing_data()
    target_tickers = get_target_tickers(stock_universe,existing_tickers,existing_unavaialble_tickers)
    
    if refresh: 
        updated_ratios_df, updated_metrics_df, updated_unavailable_tickers_df = load_new_ratios(existing_ratios_df,existing_metrics_df,target_tickers,existing_unavaialble_tickers_df)
        income_stmt_df,balance_sheet_df,cashflow_stmt_df, financial_estimate_df, comparables_df = load_new_financials(existing_income_statement, existing_balance_sheet, existing_cash_flow, existing_financial_estimates, existing_comparable_companies, target_tickers, API_KEY)
        df = create_scoring_metrics(updated_ratios_df,updated_metrics_df)
        ranked_df = rank_stocks(df)
        market_data_df = pull_market_data(ranked_df)
        multiples_df = pull_multiples(comparables_df)
        analyst_price_df = get_analyst_price_target(ranked_df,API_KEY)
        analyst_summary_df = get_analyst_grade(ranked_df,API_KEY)
        save_fmp_data(updated_ratios_df,updated_metrics_df,income_stmt_df,balance_sheet_df,cashflow_stmt_df,financial_estimate_df,market_data_df,comparables_df,multiples_df,updated_unavailable_tickers_df,analyst_price_df,analyst_summary_df)
    else:
        ratios_df, metrics_df, income_stmt_df, balance_sheet_df, cashflow_stmt_df, financial_estimate_df, market_data_df, comparables_df, multiples_df,analyst_price_df,analyst_summary_df = read_fundamental_data()
        df = create_scoring_metrics(ratios_df,metrics_df)
        ranked_df = rank_stocks(df)
        intrinsic_values_df, sensitivity_inputs, comps_average, checking_values_df, sector_exit_multiples, checking_multiples_df = run_valuation_engine(ranked_df)
        intrinsic_values_df = sensitivity_analysis(ranked_df, comps_average)
        analyst_df = analyst_additions(analyst_price_df,analyst_summary_df)
        research_output_df, optimized_universe = valuation_summary(market_data_df,intrinsic_values_df,analyst_df)

        # Sensitivity Analysis 
        # sensitivity_matrix(sensitivity_inputs['valuation_df'],sensitivity_inputs['balance_sheet'],sensitivity_inputs['income_statement'],sensitivity_inputs['WACC'],'ADBE')

        # Efficient Frontier 
        cov_matrix,expected_returns, risk_free_rate = get_mpt_data(research_output_df)
        optimal_sharpe,optimal_weights,optimal_return,optimal_volatility = optimize_max_sharpe(cov_matrix,expected_returns,risk_free_rate)

        # Output Section

        # show_ranked_stocks(ranked_df)
        # print()
        checking_margins(checking_values_df)
        print()
        checking_valuation_multiples(metrics_df, market_data_df, sector_exit_multiples, checking_multiples_df)
        print()
        show_valuation_report(research_output_df)
        print()
        # show_efficient_frontier(optimal_sharpe,optimal_weights,optimal_return,optimal_volatility)
       

    
        
        


    

       


execution()
