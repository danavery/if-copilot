import requests


class ZMachineClient:
    def __init__(self, scheme="http", server="localhost", port=3000):
        self.base_endpoint = f"{scheme}://{server}:{port}/"

    def get_titles(self):
        endpoint = self.base_endpoint + "titles"
        method = "GET"
        return self._make_request(endpoint, method)

    def new_game(self, game="Zork 1.z5", label="default"):
        endpoint = self.base_endpoint + "games"
        method = "POST"
        payload = {"game": game, "label": label}
        return self._make_request(endpoint, method, payload)

    def delete_game(self, game_pid):
        endpoint = self.base_endpoint + f"games/{game_pid}"
        method = "DELETE"
        return self._make_request(endpoint, method)

    def action(self, game_pid, command):
        endpoint = self.base_endpoint + f"games/{game_pid}/action"
        method = "POST"
        payload = {"action": command}
        return self._make_request(endpoint, method, payload)

    def _make_request(self, endpoint, method, payload=None):
        if method == "GET":
            response = requests.get(endpoint)
        if method == "POST":
            response = requests.post(endpoint, json=payload)
        if method == "DELETE":
            response = requests.delete(endpoint)
            return
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"error: {response}")
            data = ""
        return data


if __name__ == "__main__":
    client = ZMachineClient()
    print(client.get_titles())
    new_game = client.new_game()
    game_pid = new_game["pid"]
    print(client.action(game_pid, "open mailbox"))
