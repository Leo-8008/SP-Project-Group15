#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Define the lists of stock groups
fang_stocks = ['META', 'AMZN', 'NFLX', 'GOOGL', 'BTC-USD']
bluechip_stocks = ['ALV', 'KO', 'MCD', 'V', 'BTC-USD']
finance_stocks = ['JPM', 'GS', 'CS', 'UBS', 'BTC-USD']
energy_stocks = ['XOM', 'CVX', 'BP', 'SHEL', 'BTC-USD']
tech_stocks = ['TSLA', 'NVDA', 'ZM', 'SHOP', 'BTC-USD']

# Combine all stocks into a single list
all_stocks = fang_stocks + bluechip_stocks + finance_stocks + energy_stocks + tech_stocks

# Create a SQLite database connection
conn = sqlite3.connect('stocks.db')

app = Flask(__name__)

def plot_corr(group_name, stocks, conn):
    # Query the closing prices for the group of stocks
    columns = ', '.join([f'"{stock}"' for stock in stocks])
    query = f"SELECT Date, {columns} FROM closing_prices"
    group_prices = pd.read_sql_query(query, conn, index_col='Date', parse_dates=['Date'])
    # Calculate the correlation matrix for the group of stocks
    corr_matrix = group_prices.corr()
    # Plot the correlation matrix
    plt.figure(figsize=(8, 8))
    plt.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar()
    plt.title(f'Correlation Matrix of {group_name} Stocks')
    plt.xticks(range(len(stocks)), stocks, rotation=45)
    plt.yticks(range(len(stocks)), stocks)
    # Add numerical values to the plot
    for i in range(len(stocks)):
        for j in range(len(stocks)):
            plt.text(i, j, round(corr_matrix.iloc[i, j], 2), ha='center', va='center', color='white')
    plt.tight_layout()
    fig = plt.gcf()
    return fig


def download_data(stocks, conn):
    data = yf.download(stocks, start="2020-01-01", end="2023-04-29")
    closing_prices = data['Close']
    closing_prices.to_sql('closing_prices', conn, if_exists='replace')

@app.route('/')
def home():
    # Create a SQLite database connection
    conn = sqlite3.connect('stocks.db')
    # Download data and create database
    download_data(all_stocks, conn)

    # Define a dictionary with stock groups
    stock_groups = {
        'FANG': fang_stocks,
        'Blue Chip': bluechip_stocks,
        'Finance': finance_stocks,
        'Energy': energy_stocks,
        'Tech': tech_stocks,
    }

    image_strings = []
    for group_name, stocks in stock_groups.items():
        # Plot correlation matrix for each group
        fig = plot_corr(group_name, stocks, conn)
        # Convert plot to PNG image
        png_image = BytesIO()
        fig.savefig(png_image, format='png')
        # Encode PNG image to base64 string
        png_image_b64_string = "data:image/png;base64,"
        png_image_b64_string += base64.b64encode(png_image.getvalue()).decode('utf8')
        image_strings.append(png_image_b64_string)

    # Close the database connection
    conn.close()

    return render_template('index.html', images=image_strings)

if __name__ == '__main__':
    app.run(port=8080)
