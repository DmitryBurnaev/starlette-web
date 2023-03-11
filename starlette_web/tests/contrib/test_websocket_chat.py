import time


def test_websocket_chat(client):
    response_pool_1 = []
    response_pool_2 = []

    with client.websocket_connect("/ws/test_websocket_chat") as websocket:
        with client.websocket_connect("/ws/test_websocket_chat") as websocket_2:

            def receive():
                nonlocal response_pool_1, response_pool_2
                response_pool_1.append(websocket.receive_json())
                response_pool_2.append(websocket_2.receive_json())

            websocket.send_json({"request_type": "connect"})
            websocket.send_json({"request_type": "publish", "message": "Unreceived message 1"})
            websocket.receive_json()
            websocket.send_json({"request_type": "publish", "message": "Unreceived message 2"})
            websocket.receive_json()
            websocket_2.send_json({"request_type": "connect"})

            # If send message immediately after
            # websocket_2 initialized, it may skip the message
            time.sleep(0.1)

            websocket.send_json({"request_type": "publish", "message": "Hello there!"})
            receive()

            websocket_2.send_json({"request_type": "publish", "message": "General Kenobi!"})
            receive()

            websocket_2.send_json(
                {"request_type": "publish", "message": "I will deal with this Jedi slime myself."}
            )
            receive()

            websocket.send_json({"request_type": "publish", "message": "Your move."})
            receive()

            websocket_2.close(1001)

        websocket.close(1001)

    all_responses = [
        "Hello there!",
        "General Kenobi!",
        "I will deal with this Jedi slime myself.",
        "Your move.",
    ]
    assert response_pool_1 == all_responses
    assert response_pool_2 == all_responses
