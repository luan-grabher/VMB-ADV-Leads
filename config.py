import json

def getConfig():
    with open('config.json', encoding='utf-8') as json_file:
        return json.load(json_file)
    
if __name__ == "__main__":
    config = getConfig()
    print(config)