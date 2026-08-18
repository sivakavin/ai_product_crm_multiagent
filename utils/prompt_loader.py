import yaml

def load_prompt(name:str) ->dict:
    with open(f"prompts/{name}.yaml","r") as f:
        return yaml.safe_load(f)

def build_prompt(name:str,**kwargs) ->str:
    data = load_prompt(name)
    system = data.get("system","")
    template = data["template"].format(**kwargs)
    return system+"\n"+template