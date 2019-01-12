if __name__ == '__main__':
    with open('avg_log.txt', 'r') as file:
        header = True
        data = []
        for line in file.readlines():
            if header:
                header = False
                continue
            data.append(line.split('\n')[0].split(','))
        
        sum_ = sum([float(x[0]) for x in data])
        avg_height = sum_/len(data)
        print('Avg height: {:.2f} cm'.format(avg_height))

