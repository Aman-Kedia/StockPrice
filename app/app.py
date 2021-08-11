import requests
from bs4 import BeautifulSoup
import pymysql
import smtplib
from email.message import EmailMessage
from config import *

def handler(event, context):
    endpoint = db_endpoint
    username = db_username
    password = db_password
    database_name = db_name

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'}
    url = ['https://in.finance.yahoo.com/quote/RELIANCE.NS/', 'https://in.finance.yahoo.com/quote/TCS.NS/', 
    'https://in.finance.yahoo.com/quote/INFY.NS/', 'https://in.finance.yahoo.com/quote/HDFC.NS/', 'https://finance.yahoo.com/quote/ADANIENT.NS/']

    stocks = ['Reliance', 'TCS', 'Infosys', 'HDFC', 'AdaniEnt']
    
    connection = pymysql.connect(host=endpoint, user=username, passwd=password, db=database_name, port=3306)
    cursor = connection.cursor()

    for i in range(5):
        r = requests.get(url[i], headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        price = soup.find('div', {'class': 'D(ib) Mend(20px)'}).find_all('span')[0].text
        curtime = soup.find('div', {'class': 'C($tertiaryColor) D(b) Fz(12px) Fw(n) Mstart(0)--mobpsm Mt(6px)--mobpsm'}).find_all('span')[0].text
        curtime = list(curtime.split())
        if curtime[0] == "As":
            curtime = curtime[2][:-2]
        else:
            curtime = curtime[-2][:-2]
        x = curtime.find(':')
        if curtime[:x] in ['1','2','3']:
            curtime = str(int(curtime[0])+12) + curtime[1:]
        else:
            curtime = '0' + curtime
        curtime += ':00'
        price = str(price)
        price = price[0] + price[2:]
        price = float(price)
        
        cursor.execute(f'SELECT Price, Ctime from {stocks[i]} where id = (SELECT max(id) from {stocks[i]})')
        rows = cursor.fetchall()

        previous_price = float(rows[0][0])
        previous_time = str(rows[0][1])

        if curtime != previous_time:
            cursor.execute(f"INSERT INTO {stocks[i]} (Price, Ctime, Cdate) VALUES ({price}, '{curtime}', CURDATE())")

        if curtime != previous_time:
            if price <= (previous_price-10) or price >= (previous_price+10):
                Email_Addr = email_addr
                Email_pass = email_pass
                msg = EmailMessage()
                msg['Subject'] = "Hey Aman! Your stock buddy here..."
                msg['From'] = 'Stock Buddy'
                msg['To'] = to_email_addr
                if price <= (previous_price-10):
                    msg.set_content(f"The Current stock price for {stocks[i]} is {price}\nYou might consider buying some shares.\nHappy Trading!!")
                else:
                    msg.set_content(f"The Current stock price for {stocks[i]} is {price}\nYou can sell your shares or maybe consider selling some in advance shares.\nHappy Trading!!")
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(Email_Addr, Email_pass)
                    smtp.send_message(msg)
    
    connection.commit()
    cursor.close()
    return "Data inserted successfully..."