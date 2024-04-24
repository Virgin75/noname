import modal

users = modal.App("users")


@users.function()
def func_users():
    print("This code is running on a remote worker!")
    return 1
