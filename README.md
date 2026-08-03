# Python Equity Research & Portfolio Construction Engine
A Python-based equity research engine that automates stock screening, financial forecasting, intrinsic valuation, and portfolio construction.

## Overview

This project automates the equity research process by collecting financial data, forecasting company performance, estimating intrinsic value, and building investment portfolios.

It combines historical financial statements, analyst estimates, discounted cash flow (DCF) valuation, comparable company analysis, scenario analysis, and validation checks to evaluate stocks and identify potential investment opportunities.

## Key Features

### Data Collection
- Automated financial statement collection
- Analyst revenue estimates
- Market and valuation data
- Comparable company identification

### Financial Analysis
- Historical revenue and margin analysis
- Working capital analysis
- Capital expenditure analysis
- Financial ratio analysis

### Sanity Checks
- Missing financial data detection
- Unsupported industry filtering
- Financial statement validation
- Tax rate validation
- Revenue and margin consistency checks

### Forecasting Engine
- Analyst estimate integration
- Revenue growth forecasting
- Growth decay methodology
- Margin convergence assumptions
- Operating leverage analysis
- Data quality validation

### Valuation
- Multi-stage Discounted Cash Flow (DCF)
- Perpetuity Growth Method
- Exit Multiple Method
- Comparable Company Analysis (Comps)
- Sensitivity & Scenario Analysis

### Validation
- Valuation assumption checks
- Margin validation
- Terminal value validation
- Sector multiple validation
- Intrinsic value comparison

### Portfolio Construction
- Stock screening and ranking
- Mean-Variance Optimization (Modern Portfolio Theory)
- Efficient Frontier portfolio construction

## Example Research Output
![Example Research Output](example_research_output.png)

## Tech Stack
- Pandas
- NumPy
- yfinance
- matplotlib
- seaborn
- Financial Modeling Prep API

![Sensitivity Analysis Heat Map](Sensitivity_Analsysis_HeatMap.png)


## Roadmap
### Completed

- Historical statement integration
- Revenue forecasting framework
- Cost Schedule forecasting (COGS & SG&A)
- UFCF forecasting
- WACC calculation
- Analyst estimate integration
- Terminal value calculation
- Sensitivity Analysis
### In Progress
- Margin convergence modeling
### Planned
- Monte Carlo simulation
- Comparable company valuation
- Automated stock screener integration
Disclaimer,

This project is intended for educational and research purposes only and should not be considered investment advice.
