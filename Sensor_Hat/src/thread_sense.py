import threading
import time
import math
from random import randint
from sense_hat import SenseHat, ACTION_PRESSED, ACTION_HELD, ACTION_RELEASED
sense = SenseHat()

G = [0, 127, 0]  # Green
R = [127, 0, 0]  # Red

# Segno verde: visualizzato al termine del programma
green_sign = [
G, G, G, G, G, G, G, G,
G, G, G, R, R, G, G, G,
G, G, R, G, G, R, G, G,
G, R, G, G, G, G, R, G,
G, R, G, G, G, G, R, G,
G, G, R, G, G, R, G, G,
G, G, G, R, R, G, G, G,
G, G, G, G, G, G, G, G
]

exit_flag = (0)


# Alla pressione del pulsante del sense-hat il programma termina
def pushed_middle(event):
    global exit_flag
    if event.action == ACTION_PRESSED:
        print("Button pressed")
        exit_flag = 1

class Measure(object):
    def __init__(self, channel, value, timestamp, processed):
        self.channel = channel
        self.value = value
        self.timestamp = timestamp
        self.processed = processed

# Classe per eseguire la calibrazione iniziale
class Calibration():

    def __init__(self, name, pcycles=5, pmin=0, pmax=100):
        self.name = name
        self.pcycles = pcycles
        self.pmin = pmin
        self.pmax = pmax

    def calibrate(self):

        avg_temp = 0
        calib = 1

        # Avvio fase di calibrazione iniziale: la temperatura media risulta
        # da una media di 5 rilevazioni della temperatura ambiente
        print("Calibrating " + self.name)

        while (calib <= self.pcycles):
            avg_temp = avg_temp + sense.get_temperature()
            print ("Calibration [" + str(calib) + "]: <" + str(avg_temp / calib) + ">")
            calib = calib + 1
            time.sleep(1)

        avg_temp = avg_temp / self.pcycles
        print ("Avg: <" + str(avg_temp)+ ">")

        # Fisso i valori di riferimento del range di temperatura
        # (+/- 1C rispetto alla temperatura di calibrazione)
        self.pmax = avg_temp + 1
        self.pmin = avg_temp - 1
        print ("Min: <" + str(self.pmin)+ ">; Max: <" +str(self.pmax)+ ">")

class StartThread(threading.Thread):

    def __init__(self, threadID, name, delay, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.delay = delay

    def run(self):

        # Avvio il thread di acquisizione
        print("Starting " + self.name)
        if self.threadID == 1:
            self.read_sesors(self.name, self.delay, self.counter)
        if self.threadID == 2:
            self.parse_measures(self.name, self.delay, self.counter)
        print("Started " + self.name)

    # Thread per la lettura dei sensori
    def read_sesors(self, threadName, delay, counter):

        global exit_flag
        global measure_list

        while counter:
            # Verifico se ho premuto il pulsante di stop
            sense.stick.direction_middle = pushed_middle

            # Se ho premuto il pulsante, esco e visualizzo
            # il segno verde
            if (exit_flag == 1):
                threadName.exit()

            # Lettura dai sensori del SenseHat acquisizione Temperatura, Pressione, Humidity
            t = sense.get_temperature()

            # Arrotondamento ad una cifra decimale
            t = round(t, 2)

            # Rilevo il timestamp
            ts = time.time()

            mis = Measure(1, t, ts, 0)

            # Aggiungo alla lista misure
            measure_list.append(mis)

            time.sleep(delay)

            counter -= 1

    # Thread per il processamento delle misure
    def parse_measures(self, threadName, delay, counter):

        global exit_flag
        global measure_list

        while counter:
            # Verifico se ho premuto il pulsante di stop
            sense.stick.direction_middle = pushed_middle

            # Se ho premuto il pulsante, esco e visualizzo
            # il segno verde
            if (exit_flag == 1):
                threadName.exit()

            # Numero misure contate
            val_count = 0
            val_tot = 0
            val_ts = 0
            val_avg = 0

            # Estraggo le misure e calcolo la media
            for mis in measure_list:
                if (mis.processed == 1):
                    measure_list.remove(mis)
                else:
                    if (val_ts == 0):                    
                        val_ts = mis.timestamp
                    val_count = val_count + 1
                    val_tot = val_tot + mis.value
                    mis.processed = 1

            if (val_count > 0):
                val_avg = val_tot / val_count
            else:
                val_avg = 0

            # Stampo il valore della media
            print("TS: <" + str(val_ts) + ">; NUM:<" + str(val_count)+ ">; AVG:<" + str(val_avg)+ ">")

            # Coloro il display in funzione della media rilevata
            self.show_temperature(val_avg)

            time.sleep(delay)

            counter -= 1

    def show_temperature(self, temp_value):

        global calib

        # Calcolo il livello di colore (tra 1 e 255) proporzionale alla temperatura rilevata
        pixel_light = int( (((temp_value - calib.pmin) / (calib.pmax - calib.pmin)) * 255) // 1)
        if (pixel_light > 255):
            pixel_light = 255
        if (pixel_light < 0):
            pixel_light = 0

        # Creo il codice colore di riferimento:
        # Blu = freddo; Rosso = caldo
        X = [pixel_light, 0, 255 - pixel_light]

        one_level = [
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X,
        X, X, X, X, X, X, X, X
        ]
        
        # Coloro il display in tinta unita
        sense.set_pixels(one_level)

# Creo la lista per la storicizzazione delle misure
measure_list =  []

# Eseguo la calibrazione iniziale
calib = Calibration("SenseHat-Temp")

# Create new threads
th_acquisition = StartThread(1, "Acquisition", 0.5, 500)
th_process = StartThread(2, "Process", 5, 50)

# Start new Threads
th_acquisition.start()
th_process.start()

th_acquisition.join()
th_process.join()

sense.set_pixels(green_sign)
print("Termine programma")
