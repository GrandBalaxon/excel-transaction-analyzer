import datetime

str_ = "31.12.2021 16:44:00"
date = datetime.datetime.strptime(str_, "%d-%m-%Y %H:%M:%S")
print(date)
