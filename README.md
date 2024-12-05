# Media_Play_Controller

#############################################################################################################################
Документация по исходным кодам MS:
#https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession?view=winrt-26100

Приложение для управления мультимедией Windows 10, редакция от 1809 и Windows 11 

Приложение имеет интерфейс поверх панели задач, которое выводит основную информацию о медиа в системе.
Интерфейс приложения можно скрыть комбинацией клавишь "ctrl + down" и показать "ctrl + up" или с помощью клавиши, и вернуть обратно иконкой из трея.
Так же можно поставить на паузу "ctrl + space" или клавишей пауза в окне.
Переключать треки вперёд/нахад можно клавишами "ctrl + left" и "ctrl + right" или клавишами в приложении.

Возможности улучшения:
Если свойства медиа доступны, то можно извлечь так же  ещё и эти данные
#    'album_artist': str,
#    'album_title': str,
#    'album_track_count': int,
#    'artist': str,
#    'genres': list,
#    'playback_type': int,
#    'subtitle': str,
#    'thumbnail':
#        <_winrt_Windows_Storage_Streams.IRandomAccessStreamReference object at ?>,
#    'title': str,
#    'track_number': int,

#перемотка на хх секунд, если есть возможность получить время проигрывания
#player_time = 10 
#media_session.try_change_playback_position_async_async_async(player_time*10000000) # в тиках
#print("Позиция 10 сек.")

#Можно добавить возможность менять повтор.
#TryChangeAutoRepeatModeAsync(MediaPlaybackAutoRepeatMode)
