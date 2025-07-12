import datetime
import json
import logging
import os
import sys
from pathlib import Path

from src.reports import get_transactions_df, spending_by_category
from src.services import calculate_category_cashback
from src.utils import get_data_from_excel
from src.views import get_main_page_data

logger = logging.getLogger("main")


def clear_console() -> None:
    """ Функция очистки консоли. """
    os.system("cls" if os.name == "nt" else "clear")


def main() -> None:
    """ Точка входа программы. """
    clear_console()

    print(
        "Добро пожаловать в анализатор банковских транзакций.\n"
        "\nПеред началом убедитесь, что вы указали правильный API-key в файле '.env'"
        "\nА также, что в файле 'user_settings.json' указаны верные данные.\n"
    )

    input("Нажмите Enter, чтобы продолжить: ")
    clear_console()

    # 1. Получение пути к файлу
    while True:
        print(
            "Для начала необходимо указать имя Excel-файла, расположенного в папке 'data'.\n"
            "\nПри работе со стандартным файлом 'operations.xlsx' оставьте поле ввода пустым."
        )

        excel_file_name = input("\nВведите имя файла: ")

        if excel_file_name and excel_file_name != "operations.xlsx":
            excel_file_path = Path(__file__).parent / "data" / excel_file_name

            if excel_file_path.exists():
                print("\nФайл найден.")
                standard_operations_file_flag = False
                break
            else:
                print("\nФайл не найден. Пожалуйста, введите корректный путь.")
                input("\nНажмите Enter, чтобы продолжить: ")
                clear_console()

        else:
            excel_file_path = Path(__file__).parent / "data" / "operations.xlsx"
            print("\nРабота со стандартным файлом операций.")
            standard_operations_file_flag = True
            break

    # 2. Загрузка данных
    transactions_df = get_transactions_df(excel_file_path)
    if transactions_df is None:
        print("Программа: Ошибка при загрузке данных из Excel.")
        sys.exit(1)
    else:
        print("\nДанные файла успешно загружены.")
        input("\nНажмите Enter, чтобы продолжить: ")

    # 3. Основное меню анализа
    while True:
        clear_console()

        print(
            "Выберите действие:\n"
            "1. Показать расходы по категории\n"
            "2. Рассчитать кэшбэк по категориям\n"
            "3. Показать данные для главной страницы (сводка)\n"
            "4. Выйти\n"
        )

        action = input("Пользователь: ")

        # Анализ расходов по категории
        if action == '1':
            clear_console()
            print("Анализ расходов по категории.\n")

            category = input("Введите категорию для анализа: ")
            year = int(input("Введите год: "))
            month = int(input("Введите месяц: "))
            day = int(input("Введите день: "))

            spending_data = spending_by_category(
                transactions_df, category,  datetime.datetime(year, month, day)
            )

            if spending_data:
                print(f"\nРасходы по категории '{category}':")

                for transaction in spending_data:
                    print(json.dumps(transaction, indent=4, ensure_ascii=False))

                input("\nНажмите Enter, чтобы продолжить: ")

            else:
                print(f"\nНе удалось получить данные о расходах по категории '{category}'.")
                input("\nНажмите Enter, чтобы продолжить: ")

        # Расчет кэшбэка
        elif action == '2':
            clear_console()
            print("Расчет кэшбэка.\n")

            year = int(input("Введите год: "))
            month_str = input("Пользователь: Введите месяц (или оставьте пустым для всего года): ")
            month = int(month_str) if month_str else None

            transactions_list = get_data_from_excel(excel_file_path)
            cashback_data = calculate_category_cashback(transactions_list, year, month)
            data = json.loads(cashback_data)

            if cashback_data:
                print(
                    f"\nСуммарный кэшбэк в указанный период по категориям:\n",
                    json.dumps(data, indent=4, ensure_ascii=False)
                )
                input("\nНажмите Enter, чтобы продолжить: ")

            else:
                print("\nНе удалось рассчитать кэшбэк.")
                input("\nНажмите Enter, чтобы продолжить: ")

        # Получение данных для главной страницы
        elif action == '3':
            while True:
                clear_console()
                print(
                    "Получение данных для главной страницы (сводка).\n",
                    "\nНеобходимо указать дату.",
                    "\nВведите любой символ, чтобы перейти к вводу даты, либо оставьте поле пустым, чтобы взять текущую.\n"
                )

                user_input = input("Пользователь: ")
                if user_input:
                    if standard_operations_file_flag:
                        print("\nВременный рамки стандартного файла транзакций: 01.01.2018 - 31.12.2021")

                    year = int(input("\nВведите год: "))
                    month = int(input("Введите месяц: "))
                    day = int(input("Введите день: "))
                    try:
                        date = datetime.datetime(year, month, day)
                        break
                    except Exception as e:
                        print(f"Ошибка: {str(e)}")
                        input("\nНажмите Enter, чтобы продолжить: ")
                else:
                    date = datetime.datetime.now()
                    break

            date_time_str = date.strftime("%Y-%m-%d %H:%M:%S")
            transactions_list = get_data_from_excel(excel_file_path)

            main_page_data = get_main_page_data(date_time_str, transactions_list)
            data = json.loads(main_page_data)

            if main_page_data:
                print(
                    f"\nДанные для главной страницы за {date_time_str}:\n",
                    json.dumps(data, indent=4, ensure_ascii=False)
                )
                input("\nНажмите Enter, чтобы продолжить: ")
            else:
                print("\nНе удалось получить данные для главной страницы.")
                input("\nНажмите Enter, чтобы продолжить: ")

        elif action == '4':
            print("\nЗавершение работы.\n")
            break

        else:
            print("\nНеверный ввод. Пожалуйста, выберите действие из списка.")
            input("\nНажмите Enter, чтобы продолжить: ")


if __name__ == "__main__":
    main()
