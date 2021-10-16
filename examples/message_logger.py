from licord import Gateway, find_token

gateway = Gateway(token=find_token())

while True:
    payload = gateway.recv()
    match payload.get("t"):
        case "MESSAGE_CREATE":
            print(f"{payload['d'][b'author'][b'username'].decode()}"
                  f"#{payload['d'][b'author'][b'discriminator'].decode()}: "
                  f"{payload['d'][b'content'].decode()}")
                
        case "MESSAGE_UPDATE":
            print(f"{payload['d'][b'author'][b'username'].decode()}"
                  f"#{payload['d'][b'author'][b'discriminator'].decode()} (edit): "
                  f"{payload['d'][b'content'].decode()}")