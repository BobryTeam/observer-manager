from typing import Dict
from queue import Queue

from threading import Thread

import time

from events.event import *
from events.kafka_event import *

from trend_data.trend_data import TrendData

from microservice.microservice import Microservice


class ObserverManager(Microservice):
    '''
    Класс отвечающий за представление Observer manager
    Его задача -- отправлять запрос на проведение анализа, пересылать полученные данные Desicion module, отправлять запрос на сбор метрик
    '''
    
    TIMER_SEND_GET_METRICS_EVENT = 300.0


    def __init__(self, event_queue: Queue, writers: Dict[str, KafkaEventWriter]):
        '''
        Инициализация класса:
        `self.main_thread` - основной поток с главным лупом проекта
        '''
        super().__init__(event_queue, writers)

        self.main_thread = Thread(target=self.send_get_metrics_event)
        self.main_thread.start()

    def send_get_metrics_event(self):
        '''
        Отправка ивента на сбор метрик
        '''
        while True:
            time.sleep(self.TIMER_SEND_GET_METRICS_EVENT)
            self.writers['mtrc'].send_event(Event(EventType.GetMetrics, ''))

    def handle_event(self, event: Event):
        '''
        Обработка ивентов
        '''
        target_function = None

        match event.type:
            case EventType.GotMetrics:
                target_function = self.handle_event_got_metrics
            case EventType.TrendData:
                target_function = self.handle_event_trend_data
            case _:
                pass

        if target_function is not None:
            Thread(target=target_function, args=(event.data,)).start()

    def handle_event_got_metrics(self, _):
        self.writers['tran'].send_event(Event(EventType.AnalyseTrend, ''))

    def handle_event_trend_data(self, trend_data: TrendData):
        # send TrendData to DM Manager
        self.writers['dmm'].send_event(Event(EventType.TrendData, trend_data))
