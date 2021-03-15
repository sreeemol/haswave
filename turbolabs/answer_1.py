

def server_cost(d1, m1, y1, d2, m2, y2):
    if y1==y2:
        if m2==m1:
            if d2==d1:
                cost=20
            else:
                dif=d2-d1
                cost=dif*30
        else:
            dif=m2-m1
            cost=dif*100
    else:
        dif=y2-y1
        cost=dif*20000
    return cost


if __name__ == '__main__':
    
    d1M1Y1 = input().split()
    d1 = int(d1M1Y1[0])
    m1 = int(d1M1Y1[1])
    y1 = int(d1M1Y1[2])

    d2M2Y2 = input().split()
    d2 = int(d2M2Y2[0])
    m2 = int(d2M2Y2[1])
    y2 = int(d2M2Y2[2])

        
    result = server_cost(d1, m1, y1, d2, m2, y2)
    print(str(result) + '\n')
