import numpy
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

ecg_data = numpy.load("ecg_data.npy")

rotated = numpy.rot90(ecg_data, -1)

x_times = [datetime.datetime.fromtimestamp(time / 1e9) for time in rotated[1]]

figure = plt.figure()
ax = figure.add_subplot(1, 1, 1)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%S"))
ax.xaxis.set_major_locator(mdates.SecondLocator())

plt.plot(x_times, rotated[0])

plt.xlabel("Time")
plt.ylabel("Voltage (μV)")

plt.gcf().autofmt_xdate()
plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter("%d μV"))

plt.show()
