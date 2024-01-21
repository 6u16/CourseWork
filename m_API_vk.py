import requests
import json
from urllib.parse import urlencode  # urlencode - метод который превратит наш словарь params в валидные параметры URL
import os
import shutil # для удаления папки с содержимым
import PySimpleGUI as sg # интерфейс

# Курсовая работа 'Резервное копирование'

# в релизе обнулить значения токенов и user_id
token_Vk = ''
user_id = ''
token_Yd = ''


class APIvk_client:  # класс для взаимодействия с вк
    APIbase_url = 'https://api.vk.com/method' # базовый URL
    
    def __init__(self, token, user_id) -> None:  # в инициаты заводим токен, всегда нужен конкретного пользователя для работы приложения
        self.token = token
        self.use_id = user_id  # это поле в строке тоже обязательно так как и токен, он будет пренадлежать конкретному пользователю, который рботает с нашим приложением 
        self.cntr_01 = 0  # Счётчик скачанных фото
        
    def _build_url(self, api_method): # метод построения URL всегда одинаков, за искл. метода API (status.set, photos.get, и тд)
        return f'{self.APIbase_url}/{api_method}'
    
    def get_common_params(self):  # медод класса для вставки параметров acces_token и v - version ОБЯЗАТЕЛЬНЫ
        return {
            'access_token': self.token,
            'v': '5.131'
        }
    
    alboms_id = []
    alboms_id_dict = {}

    def get_albums_list(self): # возвращаем список доступных альбомов
        params = self.get_common_params() # параметры нужны для каждого запроса, поэтому вызовем их здесь
        params.update({'user_id': self.use_id}) # добавляем параметры для использования метода 'photos.getAlbums' - как указано в документации
        response = requests.get(self._build_url('photos.getAlbums'), params=params)  # 'photos.getAlbums' - метод для получения json альбома из vk
        
        if response.json().get('error', {}): # Проверка на правильность токена и user_id
            return response.json()
        else:
            temp_albID = response.json().get('response', {}).get('items', {}) # пробираемся к альбомам(они - список)
            text_01 = []
            print('Список альбомов:')
            #print(response.json())
            for element in temp_albID: 
                self.alboms_id_dict.setdefault(element.get('title', {}), [element.get('id', {}), element.get('size', {})]) # формируем словарь ключ = название альбома, значение = id и кол.фото
                text_01.append(['Название: ' + str(element.get('title', {})),\
                    'Id: ' + str(element.get('id', {})),\
                    'фотографий: ' + str(element.get('size', {}))])
            return text_01
    
    def get_foto_from_album(self, album_name, value_of_files, size):  # Скачиваем фото по album_name, value_of_files, size(будет скачан указанный или наибольший имеющийся)
        params = self.get_common_params() # параметры нужны для каждого запроса, поэтому вызовем их здесь
        try: # Проверка правильности введённых данных
            params.update({'owner_id': self.use_id, 'album_id': self.alboms_id_dict.get(album_name)[0], 'extended': 1})  # alboms_id_dict -> по ключу имени альбома берём Id из списка[0], 'extended': 1 - расширенная инфа(лайки)
            response = requests.get(self._build_url('photos.get'), params=params)  # 'photos.get' - метод для получения фото профиля из vk
            
            # информационный json по фото из альбома
            #with open('Data_files/photos_infoVK_from_album_w.json', 'w', encoding='utf-8') as f:  # фото инфо в json по всем фоткам из альбома
            #    json.dump(response.json(), f, ensure_ascii=False, indent=3)
            
            # Проверка на наличие пути 'Images/{album_name}', если элемента нет, то создаём, или пропускаем
            if not os.path.isdir('Images/'):
                os.mkdir('Images/')
            if not os.path.isdir('Images/' + album_name):
                os.mkdir('Images/' + album_name)
            file_path = os.path.join(os.getcwd(), 'Images/' + album_name)
            
            if not os.path.isdir('Data_files/'): # Создание папки Data_files
                os.mkdir('Data_files/')
        
        except Exception:   
                return 'FileNameERROR or ValueERROR or AuthorizationERROR'
            
        try:  # Проверка правильности введённых данных
            output_info_list = []
            album_dict = {}
            
            photo_list = response.json().get('response', {}).get('items', {}) # формируем список фото
            for cntr, element_1 in enumerate(photo_list, start=1): # Достаём словари каждого фото
                self.cntr_01 = cntr
                for element_2 in element_1.get('sizes'):  # Листаем в словарях ключ 'sizes'                  
                    
                    if element_2.get('type') == size:  # выбираем указанный размер
                        url_01 = element_2.get('url')
                        response_01 = requests.get(url_01)  # запрашиваем адреса images
                        file_name = f'image_{cntr}_'+ str(element_1.get('likes', {}).get('count')) + '.jpg'  # Формируем имя файла
                            
                        with open(f'{file_path}/' + file_name, 'wb') as f:  # в папку попути file_path помещаем файлы по именам file_name
                            f.write(response_01.content)
    
                        temp_file_dict = {'file_name': file_name, 'size': size, 'likes': file_name[-5]}  # Словарик очередного фото
                        break # нашли рзмер и назад
                        
                    if element_2.get('type') == 'o': # если нет указанного размера то сохраняем наибоьший из доступных
                        url_01 = element.get('url') # Возвращаемся в предыдущий размер(он будет наибольшим) если достигли списков размера фото 'type': 'o' 
                        response_01 = requests.get(url_01)  # запрашиваем адреса images
                        file_name = f'image_{cntr}_'+ str(element_1.get('likes', {}).get('count')) + '.jpg'  # Формируем имя файла
                            
                        with open(f'{file_path}/' + file_name, 'wb') as f:  # в папку попути file_path помещаем файлы по именам file_name
                            f.write(response_01.content)
    
                        temp_file_dict = {'file_name': file_name, 'size': element.get('type'), 'likes': file_name[-5]}
                    
                    element = element_2 # Для хранения данных предыущего(максимального размеа), 
              
                output_info_list.append(temp_file_dict) # инфо лист с сохранёнными фото
                              
                if cntr == value_of_files: break # покидаем цикл по достижению заданного кол.фото
                    
            album_dict.setdefault(album_name, output_info_list) # словарик с названием альбома и вложенными(загруженными) фото
                
            with open(f'Data_files/photos_from_almum_{album_name}_w.json', 'w', encoding='utf-8') as f:  # фото инфо в json по всем фоткам из выбранного альбома (пригодится для загрузки в облако)
                json.dump(album_dict, f, ensure_ascii=False, indent=3)

            return album_dict
            
        except Exception:   
                return 'SizeERROR'
        
    def del_tmp(self): # удаление временных папок
        file_path = os.path.join(os.getcwd(), 'Images')
        try:
            shutil.rmtree(file_path)
        except Exception:
            return 'Каталог удалён либо не существует'
            
        
class APIyd_client(): # Класс взаимодействия с YandexDisc
    
    def __init__(self, token) -> None:  # в инициаты заводим токен, всегда нужен конкретного пользователя для работы приложения
        self.token = token
        self.cntr_01 = 0  # Счётчик загруженных фото
        self.progressbar_value = 0
        
    # загрузить файл на яндекс диск (Читаем документацию к ЯД!!!)
    def upload_to_YD(self, album_name):
        self.album_name = album_name
        
        # запрос на создание папки 'Image' 
        url = 'https://cloud-api.yandex.net/v1/disk/resources' # отдельно путь URL на яндекс диск - это именно путь для СОЗДАНИЯ ПАПКИ!!! (Докумнтация ЯД)
        params = {'path':'Image'}   # отдельно параматр, и он сохранит папку с этим именем
        headers = {'Authorization': self.token} # в заголовке передаём OAuth Token, мы его получили заранее
        response = requests.put(url, params=params, headers=headers)       
        print(response.json())
        
        # запрос на создание папки album_name в папке 'Image' 
        url = 'https://cloud-api.yandex.net/v1/disk/resources' # отдельно путь URL на яндекс диск - это именно путь для СОЗДАНИЯ ПАПКИ!!! (Докумнтация ЯД)
        params = {'path':f'Image/{album_name}'}   # отдельно параматр, и он сохранит папку с этим именем
        headers = {'Authorization': self.token} # в заголовке передаём OAuth Token, мы его получили заранее
        response = requests.put(url, params=params, headers=headers)       
        print(response.json()) 
        
        # Откроем наш json указанного аьбома = тот, что только что скачали (упростил)
        try:  # Проверка, вернёт response.json() с ошибками
            with open(f'Data_files/photos_from_almum_{album_name}_w.json', 'rt', encoding='utf-8') as f:
                json_data = json.load(f) # функция обрабочик: преобразует в словарь
            print(json_data.get(str(album_name)))
            self.progressbar_value = len(json_data.get(str(album_name)))
        
            for element in json_data.get(str(album_name)):
                file_name = element.get('file_name')
                print(file_name)
                self.cntr_01 += 1
                
                # запросить URL для загрузки
                url = 'https://cloud-api.yandex.net/v1/disk/resources/upload' # отдельно путь URL на яндекс диск - это именно ЗАГРУЗОЧНЫЙ путь
                params = {'path':f'Image/{album_name}/{file_name}'}   # отдельно параматр, и он сохранит файл с ЭТИМ ИМЕНЕМ в папке, которую мы создали ранее
                headers = {'Authorization': self.token} # в заголовке передаём OAuth Token, мы его получили заранее
                response = requests.get(url, params=params, headers=headers) # запрашиваем URL для сохранения ** придёт если мы авторизовались - это как раз OAuth Token - один из многих способов авторизации

                url_for_upload = response.json().get('href','') # Получаем из ключа 'href' URL путь для загрузки нашей картинки, лучше использовать get, так как он не крашнет нам прогу
                
                with open(f'Images\\{album_name}\\{file_name}', 'rb') as f:  # Открываем наш файл картинки в битовом формате
                    response = requests.put(url_for_upload, files={'file': f}) # И через PUT по URL в именованый параметр files=, помещаем наш файл f, с понятием для сервера 'file': 
                    print(response) # будет 201 - ОК значит 
            return json_data
        except Exception:
            return response.json()

# создадим экземпляры класса - каждый экземпляр это пользоватль
vk_client_01 = APIvk_client(token_Vk, user_id) # это я, мой id в вк 157448762
yd_client_01 = APIyd_client(token_Yd)

# Создание пользовательского интерфейса
sg.theme('DarkAmber')  # Устанавливаем цвет внутри окна 
layout_2 = [
          [sg.Button('Guide', button_color='green')],
          [sg.Text('VK', size=(15, 1)), sg.InputText('Token_VK', key='Token_VK', size=(100, 1)), sg.Text('+', size=(1, 1)), sg.InputText('user_id', key='user_id', size=(15, 1))],
          [sg.Text('YandexDisc', size=(15, 1)), sg.InputText('Token_YandexDisc', key='Token_YandexDisc', size=(100, 1))],
          #[sg.Text('GoogleDrive', size=(15, 1)), sg.InputText('Token_GoogleDrive', size=(100, 1))],
          [sg.Text('_'  * 180)],
          [sg.Button('Вывести список доступных альбомов и авторизовать пользователя'), sg.Text('<- Проверка авторизаций', size=(30, 1), text_color='white')],
          [sg.Multiline(size=(170,10), key='-LOG-'),],
          [sg.Text('Перед загрузкой необходимо вывести список доступных альбомов', key='a', text_color='red', background_color='black', enable_events=True)],
          [sg.Text('_'  * 180)],
          [sg.Text('Параметры альбома для загрузки', size=(30, 1), text_color='white')],
          [sg.Text('Выбрать альбом:'), sg.InputText('album_name', size=(15, 1), key='al_nm'), sg.Text('Номер альбома актуален для загрузки на Диск', size=(40, 1), text_color='orange')],
          [sg.Text('Кол.фотографий:'), sg.InputText('5', size=(5, 1), key='ph_val')],
          [sg.Text('Размер фото:'), sg.InputText('min_<-_s,m,x,y,z,w_->_max', size=(28, 1), key='size')],
          [sg.Button('Загрузить фото из VK в папку (Images)'), sg.Button('Удалить временные файлы')],
          [sg.Text('Загрузка в облако', size=(30, 1), text_color='white')],
          [sg.Button('Загрузить фото на YDisc')],
          [sg.Text('Файлов загружено из альбома VK:'), sg.Text(key='-Load_count-', enable_events=True), sg.ProgressBar(len(vk_client_01.alboms_id_dict), orientation='h', expand_x=True, size=(20, 20),  key='-PBAR-')],
          [sg.Text('Файлов загружено на Диск:'), sg.Text(key='-Load_count1-', enable_events=True), sg.ProgressBar(yd_client_01.progressbar_value, orientation='h', expand_x=True, size=(20, 20),  key='-PBAR1-')]
         ]

# Создаем окно
window = sg.Window('Резервное копирование VK -> YandexDisc/GoogleDisc', layout_2, size=(1024,650))
# Цикл для обработки "событий" и получения "значений" входных данных
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED: 
# если пользователь закрыл окно или нажал «Отмена»
        break
    
    if event == 'Guide':  # если нужно посмотреть гид
        with open('Guide.txt', 'rt', encoding='utf-8') as f:
            for id, element in enumerate(f):
                window['-LOG-'].update(f'{element.strip()}\n', text_color='black', append=True,)
       
    if event == 'Вывести список доступных альбомов и авторизовать пользователя':
        vk_client_01 = APIvk_client(values['Token_VK'], values['user_id'])  # 
        yd_client_01 = APIyd_client(values['Token_YandexDisc'])
        
        window['-LOG-'].update(vk_client_01.get_albums_list(), text_color='yellow', append=False)
        window['-PBAR-'].update(current_count=0)
        window['-Load_count-'].update(str(0))
        info_dict = vk_client_01.get_albums_list()
        if type(info_dict) == list:
            window['a'].update('Загрузка списка завершена, введите параметры альбома зля загрузки в папку (Image)',text_color='green')
        else:
            window['a'].update('Ошибка авторизации',text_color='red')
        
    if event == 'Загрузить фото из VK в папку (Images)':
        window['-LOG-'].update(vk_client_01.get_foto_from_album(values['al_nm'], int(values['ph_val']), values['size']), text_color='blue', append=False)
        window['-PBAR-'].update(current_count= vk_client_01.cntr_01)
        window['-Load_count-'].update(str(vk_client_01.cntr_01))
    
    if event == 'Загрузить фото на YDisc':
        
        window['-LOG-'].update(yd_client_01.upload_to_YD(values['al_nm']), text_color='black', append=False)
        window['-PBAR1-'].update(current_count= yd_client_01.cntr_01)
        window['-Load_count1-'].update(str(yd_client_01.cntr_01))
        
    if event == 'Удалить временные файлы':
        vk_client_01.del_tmp()
        window['-LOG-'].update(vk_client_01.del_tmp(), text_color='blue', append=False)
        
window.close()