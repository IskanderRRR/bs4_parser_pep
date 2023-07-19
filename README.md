# Проект парсинга pep

Парсер информации о python с **https://docs.python.org/3/** и  **https://peps.python.org/**
### Перед использованием
В корневой папке нужно созжать виртуальное окружение и установить зависимости.
```
python3 -m venv venv
```
```
pip install -r requirements.txt
```
### Программа запускается из main.py в папке ./src/
```
python3 main.py [вариант парсера] [аргументы]
```
### Встроенные парсеры
- whats-new
Парсер выводящий спсок изменений в python.
```
python3 main.py whats-new [аргументы]
```
- latest_versions
Парсер выводящий список версий python и ссылки на их документацию.
```
python3 main.py latest-versions [аргументы]
```
- download
Парсер скачивающий zip архив с документацией python в pdf формате.
```
python3 main.py download [аргументы]
```
- pep
Парсер выводящий список статусов документов pep   
и количество документов в каждом статусе. 
```
python3 main.py pep [аргументы]
```
### Аргументы
Есть возможность указывать аргументы для изменения работы программы:
примеры на *whats-new*
- -h, --help
Общая информация о командах.
```
python3 main.py -h
```
- -c, --clear-cache
Очистка кеша перед выполнением парсинга.
```
python3 main.py whats-new -c
```
- -o {pretty,file}, --output {pretty,file}
Дополнительные способы вывода данных   
pretty - выводит данные в командной строке в таблице   
file - сохраняет информацию в формате csv в папке ./results/
```
python3 main.py whats-new -o file
```
### Автор
**[Iskander Ryskulov](https://github.com/IskanderRRR)**
