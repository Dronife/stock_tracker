from bs4 import BeautifulSoup as soup
from urllib.request import urlopen as uReq, Request
from prettytable import PrettyTable
import numpy as np
import os
import pandas as pd
import pathlib
import json
from datetime import date
from datetime import datetime
os.system('cls')
urls = {
    "sma": "https://finviz.com/screener.ashx?v=111&f=ta_sma20_pa,ta_sma200_sb50,ta_sma50_sb20&ft=4&o=change",
    "hammer": 'https://finviz.com/screener.ashx?v=111&f=sh_price_u30,ta_beta_o1,ta_candlestick_h&ft=4&o=change',
    "long_lower_shadow": 'https://finviz.com/screener.ashx?v=111&f=ta_beta_o1,ta_candlestick_lls&ft=4&o=change',
    "low_market_cap": 'https://finviz.com/screener.ashx?v=111&f=cap_microunder,sh_price_u15,ta_sma20_pb20&ft=4&o=change'
}

help_commands = {
    "get": "Download stock data (you can save)",
    "read": "Read the data you saved",
    "update": "Updates existing data", 
    "stats" : "You can see the success of picked strategies"
}

update_price_url = 'https://finance.yahoo.com/quote/'
date_format = '%Y-%m-%d'
strategies = ["sma", "hammer", "long_lower_shadow", "low_market_cap"]
file_path = str(pathlib.Path(__file__).parent.absolute())
export_stocks = "sample.json"
export_strategy_change = "strategy.json"
number_of_stocks = 4 

def connect(url):
    hdr = {'User-Agent': 'Chrome/88'}
    req = Request(url, headers=hdr)
    page = uReq(req)
    page_html = page.read()
    page.close()
    page_soup = soup(page_html, "html.parser")
    return page_soup


def download_stocks(url, key, save):
    print("Starting to download data...")
    page_soup = connect(url)
    table_overview = page_soup.find("div", {"id": "screener-content"})
    table_tokens = table_overview.findAll("tr")[5]
    # print(("4 stocks of "+key+":\n"))
    table = PrettyTable()
    # print(key,"stocks")
    table.field_names = (["Token", "Price"])
    json_strategy_values = {}
    for i in range(number_of_stocks):
        tablet_row_raw = table_tokens.findAll("tr")[i+1]
        tablet_row_td_element_token = tablet_row_raw.findAll("td")[1]
        tablet_row_td_element_price = tablet_row_raw.findAll("td")[8]
        token = tablet_row_td_element_token.findAll("a")[0].text
        price = tablet_row_td_element_price.findAll("a")[0].text
        table.add_row([token, price])
        temp_object = {"Token": token, "Price": price,
                       "Current_Price": "-1", "Change": "-1", "Days": "-1", "Date":datetime.today().strftime(date_format)}
        add_element(json_strategy_values, key, temp_object)
    if(not save):
        print(table, "\n")
    return json_strategy_values


def add_element(dict, key, value):
    if key not in dict:
        dict[key] = []
    dict[key].append(value)


def export(dictionary, filename):
    path = file_path+"\\"+filename
    f = open(path, "w")
    collected_values = json.dumps(dictionary)
    f.write(collected_values)


def get_price(token):
    url_fixed = update_price_url+token
    page_soup = connect(url_fixed)
    price_div = page_soup.find("div", {"id": "quote-header-info"})
    price_element = price_div.findAll("span")[3]
    return float(price_element.text)

def days_passed_count(a):
    today = str(datetime.today().strftime(date_format))
    a =  datetime.strptime(a, date_format)
    b = datetime.strptime(today, date_format)
    delta = b - a
    return delta.days

def update():
    file_path_absolute = file_path+"\\" +export_stocks
    if(os.path.exists(file_path_absolute)):
        print("File exits!\n")
        f = open(file_path_absolute,)
        loaded_file = json.load(f)
        f.close()
 
        count = 0
        stock_list = {}
        strategy_change_list = {}
        print("Getting ready to update")
        for i in loaded_file["stocks"]:
            strategy_change = 0
            print("Updating ",count+1, "table")
            json_stocks_updated = {}
            
            for j in i[strategies[count]]:
                token = j["Token"]
                price_bought = float(j["Price"])
                current_price = get_price(token)
                change_array = pd.Series([price_bought,current_price])
                change = round(change_array.pct_change()[1],2)*100
                bought_date = j["Date"]
                days_passed = days_passed_count(bought_date)
                if(change < 3.0):
                    days_passed = -1
                if(change > 3):
                    strategy_change +=1

                temp_object = {"Token": token, "Price": price_bought,
                       "Current_Price": current_price, "Change": change, "Days": days_passed, "Date":bought_date}
                add_element(json_stocks_updated, strategies[count], temp_object)
            strategy_change_percent = round((strategy_change/number_of_stocks),2)*100
            temp_change = {"Strategy":strategies[count],"Change":strategy_change_percent}
            add_element(strategy_change_list, "strategy_change", temp_change)
            count += 1
            add_element(stock_list, "stocks", json_stocks_updated)
            print("Done updating")
        
        export(stock_list, export_stocks)
        export(strategy_change_list, export_strategy_change)
        return 0
    else:
        return print("There is no files!")


def get_stocks(stock):
    stock = stock.lower()
    save = input("Do you want to save it<y/n>: ")
    if(save == "y"):
        save = True
    else:
        save = False
    stock_list = {}
    if(stock == "all"):
        count = 1
        for i, j in urls.items():
            add_element(stock_list, "stocks", download_stocks(j, i, save))
            print("Table", count, "has been downloaded...")
            count += 1
    else:
        if (not stock in urls):
            print("Does not exists!")
            return 0
    print("Finished download successfully!")
    if(save):
        print("Exporting data....")
        export(stock_list, export_stocks)
        read()

    print(("   <-Done->"))


def stats():
    update()
    if(os.path.exists(file_path+"\\"+export_strategy_change)):
        print("File exits!\n")
        f = open(file_path+"\\"+export_strategy_change,)
        loaded_file = json.load(f)
        f.close()
        text = ["sma", "hammer", "long_lower_shadow", "low_market_cap"]

        count = 0
        table = PrettyTable()
        table.title = "Strategy change"
        table.field_names = (["Strategy", "Success in %"])
        for i in loaded_file["strategy_change"]:
            table.add_row([i["Strategy"], i["Change"]])
        print(table, "\n")
        return 0
    else:
        return print("There is no files! You first to need to update existing ones")


def read():
    if(os.path.exists(file_path+"\\"+export_stocks)):
        print("File exits!\n")
        f = open(file_path+"\\"+export_stocks,)
        loaded_file = json.load(f)
        f.close()
        text = ["sma", "hammer", "long_lower_shadow", "low_market_cap"]
        atributes = ["Token", "Price", "Current_Price", "Change", "Days"]

        count = 0
        for i in loaded_file["stocks"]:
            table = PrettyTable()
            table.title = text[count]+" stocks"
            table.field_names = (
                [" Token  ", "  Bought  ", "C_Price", "Change, %", "Days"])
            atrb_count = 0

            for j in i[text[count]]:
                table.add_row([j["Token"], j["Price"],
                               j["Current_Price"], j["Change"], j["Days"]])
            print(table, "\n")
            count += 1
        return 0
    else:
        return print("There is no files! Save parsing data!")


def check_command(command):
    os.system('cls')
    command = command.lower()
    if(command == "get"):
        stock = input("Parse data?(y/n)")
        if(stock == "y"):
            stock = "all"
            get_stocks(stock)
        else:
            return 0

    elif(command == "help"):
        print("Functions:")
        for i, j in help_commands.items():
            print("{:>8} - {:>7}".format(i, j))
    elif(command == "read"):
        read()
    elif(command == "update"):
        update()
    elif(command == "stats"):
        stats()
    elif(command == "cls"):
        os.system('cls')
        return 0
    # elif(command == "connect"):
    #     get_price("UUU")
    else:
        print("wrong command")


while(True):

    command = input("Command: ")
    check_command(command)
    print("\n\n")
