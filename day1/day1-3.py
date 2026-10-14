# i = 1
# print(f"2 X {i} = {2*i}")

# i = 2
# print(f"2 X {i} = {2*i}")

# i = 3
# print(f"2 X {i} = {2*i}")

# i = 4
# print(f"2 X {i} = {2*i}")

for dan in range(2, 5):
    for i in range(1, 5):
        print(f"{dan} X {i} = {dan*i}", end = "\t")
    print("\n=========================")

print("\n")


for dan in range(1, 10):
    for i in range(2, 10):
        print(f"{i} X {dan} = {i*dan}", end = "\t")
    print("\n")
