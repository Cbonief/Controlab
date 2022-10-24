
import csv


def save_simulation_results(results, file_name):

    def save_thread():


    with open('Results/eggs.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['Time', 'Height', 'Error', 'Action'])
        for i in range(0, len(results.time)):
            data = [
                results.time[i], results.height[i], results.error[i], results.action[i]
            ]
            writer.writerow(data)