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

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'}
    
    url = ['https://www.google.com/finance/quote/RELIANCE:NSE?sa=X&ved=2ahUKEwin6NnOztryAhWNc30KHVImBA4Q_AUoAXoECAEQAw',
           'https://www.google.com/finance/quote/ADANIENT:NSE?sa=X&ved=2ahUKEwjHuqavztryAhULfisKHXY_CoQQ_AUoAXoECAEQAw',
           'https://www.google.com/finance/quote/TCS:NSE?sa=X&ved=2ahUKEwjAoNa0ztryAhXOV30KHY2ACc0Q_AUoAXoECAEQAw', 
           'https://www.google.com/finance/quote/INFY:NSE?sa=X&ved=2ahUKEwi4yoS4ztryAhXLXisKHchYA3gQ_AUoAXoECAEQAw',
           'https://www.google.com/finance/quote/HDFC:NSE?sa=X&ved=2ahUKEwiWg4i7ztryAhXSdn0KHRrFDPwQ_AUoAXoECAEQAw']

    stocks = ['Reliance', 'AdaniEnt', 'TCS', 'Infosys', 'HDFC']
    
    connection = pymysql.connect(host=endpoint, user=username, passwd=password, db=database_name, port=3306)
    cursor = connection.cursor()

    for i in range(5):
        r = requests.get(url[i], headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        price = soup.find('div', {'class': 'YMlKec fxKbKc'}).text

        curtime = soup.find('div', {'class': 'ygUjEc'}).text
        curtime = list(curtime.split())
        
        if len(curtime[2])==7:
            curtime = curtime[2][:5] + '00'
        else:
            curtime = curtime[2][:6] + '00'
    
        x = curtime.find(':')
        if curtime[:x] in ['1','2','3']:
            curtime = str(int(curtime[:x])+12) + curtime[x:]
        elif curtime[:x] == '9':
            curtime = '0' + curtime
        price = str(price)
        price = price[1] + price[3:]
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