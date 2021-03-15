a=input("enter a string")
b=int(input("enter the number"))
c=len(a)
print(c)

if c<b :
    print("not possible .enter the number is less than string length")
else :
    print("formatting")
    print(a[b])
for b in range(c):
    if a[b]==" ":
        print(a[0:b])
        break
    else:
        b=b-1
        

    
